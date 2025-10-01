#!/usr/bin/env python3

import asyncio
import email.header
import email.parser
import imaplib
import json
import logging
import os
import subprocess
import sys
from pathlib import Path

import jsonschema
import yaml

logger = logging.getLogger(__name__)

# Define the JSON schema for the configuration file
config_schema = {
    "type": "object",
    "required": ["accounts"],
    "properties": {
        "accounts": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": [
                    "username",
                    "hostname",
                    "password_command",
                ],
                "properties": {
                    "username": {
                        "type": "string",
                        "minLength": 1,
                    },
                    "protocol": {
                        "type": "string",
                        "enum": ["imaps", "imap"],
                    },
                    "hostname": {
                        "type": "string",
                        "format": "hostname",
                    },
                    "port": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 65535,
                    },
                    "password_command": {
                        "type": "string",
                        "minLength": 1,
                    },
                    "include_mailboxes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1,
                        "uniqueItems": True,
                    },
                    "exclude_mailboxes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1,
                        "uniqueItems": True,
                    },
                },
                "additionalProperties": False,
                "allOf": [
                    {"not": {"required": ["include_mailboxes", "exclude_mailboxes"]}}
                ],
            },
        },
        "timeout": {
            "type": "integer",
            "minimum": 30,
            "maximum": 3600,
        },
    },
    "additionalProperties": False,
}


def load_config(config_path: Path):
    """Load configuration from XDG_CONFIG_HOME/imap-notifier.yaml"""
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        # Validate the configuration against the schema
        jsonschema.validate(instance=config, schema=config_schema)
        return config
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        return None
    except yaml.YAMLError as e:
        logger.error(f"Error parsing configuration file: {e}")
        return None
    except jsonschema.ValidationError as e:
        logger.error(f"Invalid configuration: {e}")
        return None


# helper function to decode MIME-encoded headers
# https://docs.python.org/3/library/email.header.html#email.header.decode_header
def decode_header(header):
    if header is None:
        return None
    parts = email.header.decode_header(header)
    decoded = ""
    for s, charset in parts:
        if isinstance(s, str):
            # already str - just append
            decoded += s
        else:
            # byte string - needs to be decoded
            if charset is None:
                charset = "ascii"
            decoded += str(s, encoding=charset)
    return decoded


class IMAPNotifier:
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    config_path = Path(xdg_config_home) / "imap-notifier.yaml"

    xdg_state_home = os.environ.get(
        "XDG_STATE_HOME", os.path.expanduser("~/.local/state")
    )
    state_file_path = Path(xdg_state_home) / "imap-notifier" / "state.json"

    def __init__(self):
        self.config = load_config(self.config_path)
        self.state = {}
        self.mail_connections = {}

        self.shutdown_event = asyncio.Event()

    def load_state(self):
        """Load last check times from state file"""
        try:
            with open(self.state_file_path, "r") as f:
                self.state = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_state(self):
        """Save last check times to state file"""
        try:
            self.state_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file_path, "w") as f:
                json.dump(self.state, f)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def get_account_id(self, account_config):
        """Generate a unique ID for an account"""
        username = account_config["username"]
        protocol = account_config.get("protocol", "imaps")
        hostname = account_config["hostname"]
        if protocol == "imaps":
            port = account_config.get("port", 993)
        else:
            port = account_config.get("port", 143)
        return f"{protocol}://{username}@{hostname}:{port}"

    def get_password(self, account_config):
        """Get password using the configured command"""
        if "password_command" in account_config:
            try:
                result = subprocess.run(
                    account_config["password_command"],
                    shell=True,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                return result.stdout.strip()
            except subprocess.CalledProcessError as e:
                logger.error(
                    f"Failed to get password for {account_config['username']}: {e}"
                )
                return None
        else:
            logger.error(
                f"No password command configured for {account_config['username']}"
            )
            return None

    def send_notification(self, message):
        """Send desktop notification for new email"""
        try:
            # Extract sender and subject
            sender = decode_header(message.get("From")) or "[Unknown Sender]"
            subject = decode_header(message.get("Subject")) or "[No Subject]"

            subprocess.run(
                [
                    "notify-send",
                    "--app-name=EmailNotification",
                    "--expire-time=3000",  # duration in ms
                    "--urgency=normal",  # critical would be shown forever
                    "--icon=mail-message-new-symbolic",
                    "--category=email.arrived",
                    "Received new email",
                    f"{sender} — {subject}",
                ],
                check=True,
            )
            logger.info(f"Notification sent for email from: {sender}")

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to send notification: {e}")
        except Exception as e:
            logger.error(f"Unexpected error sending notification: {e}")

    def is_connection_alive(self, connection, account_id):
        """Check if IMAP connection is still alive"""
        try:
            # Send a NOOP command to test the connection
            connection.noop()
            return True
        except Exception:
            logger.warning(f"Connection for account {account_id} is not alive")
            return False

    async def connect_to_account(self, account_config):
        """Establish IMAP connection for an account"""
        protocol = account_config.get("protocol", "imaps")
        hostname = account_config["hostname"]

        try:
            # Create connection based on whether it's secure (imaps) or not
            if protocol == "imaps":
                port = account_config.get("port", 993)
                client = imaplib.IMAP4_SSL(hostname, port)
            else:
                port = account_config.get("port", 143)
                client = imaplib.IMAP4(hostname, port)

            # Get password
            username = account_config["username"]
            password = self.get_password(account_config)
            if not password:
                logger.error(f"No password returned for account {username:!r}")
                return None

            client.login(username, password)

            logger.info(
                f"Connected to {protocol}://{hostname}:{port} as user {username}"
            )
            return client

        except Exception as e:
            logger.error(f"Failed to connect to {protocol}://{hostname}: {e}")
            return None

    async def get_new_emails(self, connection, account_id, mailboxes_to_process):
        """Get new emails since last check"""
        logger.debug(f"Checking {account_id} for new emails")

        # Get previous unseen emails from the state
        account_state = self.state.setdefault(account_id, {})
        previous_unseen_message_ids = set(account_state.get("unseen_message_ids", []))

        unseen_message_ids = set()
        new_emails = []

        # Process each mailbox
        for mailbox in mailboxes_to_process:
            try:
                # Remove old state data
                # TODO: remove this after some time
                if mailbox in account_state:
                    del account_state[mailbox]

                # Select mailbox
                connection.select(mailbox)

                # Search for unseen emails
                status, messages = connection.search(None, "UNSEEN")

                if status != "OK":
                    logger.error(
                        f"Failed to search emails in mailbox {mailbox} for account {account_id}"
                    )
                    continue

                email_ids = messages[0].split()

                # Process new emails
                for email_id in email_ids:
                    try:
                        # Fetch the email headers only
                        status, msg_data = connection.fetch(email_id, "(RFC822.HEADER)")

                        if status == "OK":
                            msg = email.parser.Parser().parsestr(
                                msg_data[0][1].decode("utf-8", errors="ignore")
                            )
                            # Always get a Message-ID, which uniquely identifies the message.
                            # The `email_id` obtained from IMAP is just numeric identifier in the *mailbox*,
                            # not in the whole account.
                            message_id = msg.get("Message-ID")
                            unseen_message_ids.add(message_id)
                            if message_id not in previous_unseen_message_ids:
                                new_emails.append(msg)

                    except Exception as e:
                        logger.error(f"Failed to fetch email {email_id}: {e}")
                        continue

            except Exception as e:
                logger.error(
                    f"Error processing mailbox {mailbox} for account {account_id}: {e}"
                )

        # Update IDs of unseen emails in the state
        account_state["unseen_message_ids"] = sorted(unseen_message_ids)

        return new_emails

    async def process_mailboxes(self, account_config, account_id, connection):
        """Process mailboxes for an account"""
        # Determine which mailboxes to process
        include_mailboxes = account_config.get("include_mailboxes", [])
        exclude_mailboxes = account_config.get("exclude_mailboxes", [])

        if include_mailboxes and exclude_mailboxes:
            logger.error(
                f"Both include_mailboxes and exclude_mailboxes are defined for account "
                f"{account_id}. Please specify only one of them."
            )
            return

        # If no mailboxes specified but exclude_mailboxes is defined,
        # get all mailboxes from server and filter out excluded ones
        if not include_mailboxes and exclude_mailboxes:
            try:
                # Get all mailboxes from server
                status, mailbox_list = connection.list()
                all_mailboxes = []
                if status == "OK" and mailbox_list:
                    for item in mailbox_list:
                        # Extract mailbox name from LIST response
                        mailbox_name = item.decode().split(' "/" ')[-1].strip('"')
                        all_mailboxes.append(mailbox_name)

                # Filter out excluded mailboxes
                mailboxes_to_process = [
                    mb for mb in all_mailboxes if mb not in exclude_mailboxes
                ]
            except Exception as e:
                logger.error(f"Error retrieving mailboxes from server: {e}")
                return
        elif include_mailboxes:
            # Use configured mailboxes
            mailboxes_to_process = include_mailboxes
        else:
            # Fallback to INBOX
            mailboxes_to_process = ["INBOX"]

        # Get new emails
        emails = await self.get_new_emails(connection, account_id, mailboxes_to_process)

        # Send notifications for new emails
        for message in emails:
            self.send_notification(message)

    async def process_account(self, account_config):
        """Process a single account"""
        # Generate a unique ID for the account
        account_id = self.get_account_id(account_config)

        # Check if there's an existing connection for this account
        connection = self.mail_connections.get(account_id)

        try:
            # If no connection exists or it's closed, create a new one
            if not connection or not self.is_connection_alive(connection, account_id):
                connection = await self.connect_to_account(account_config)
                if not connection:
                    return
                self.mail_connections[account_id] = connection

            # Process mailboxes for this account
            await self.process_mailboxes(account_config, account_id, connection)

            logger.debug(f"Finished processing account {account_id}")

        except Exception as e:
            logger.error(f"Error processing account {account_id}: {e}")
            # Remove failed connection from cache
            if account_id in self.mail_connections:
                del self.mail_connections[account_id]

    async def run(self):
        """Run the notifier"""

        if not self.config:
            return False

        timeout = int(self.config.get("timeout", 60))
        logger.info(f"Starting mail notifier with timeout {timeout} seconds")

        while not self.shutdown_event.is_set():
            # Process all accounts concurrently
            async with asyncio.TaskGroup() as tg:
                for account in self.config["accounts"]:
                    tg.create_task(self.process_account(account))

            # Save state after each cycle
            self.save_state()

            # Wait before next check
            await asyncio.sleep(timeout)


async def main_async():
    """Async main function"""

    # Create notifier
    notifier = IMAPNotifier()

    # Load existing state
    notifier.load_state()

    result = True
    try:
        # Run the notifier
        result = await notifier.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        # Save final state
        notifier.save_state()
        logger.info("Notifier stopped")

    if result is False:
        sys.exit(1)


def main():
    """Main function"""
    # Create event loop and run async main
    asyncio.run(main_async())


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    main()
