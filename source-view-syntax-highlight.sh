#!/bin/bash
# scrptblog - Create HTML code from Vim syntax highlighting (for use in coloring scripts)

filename=$@
background=light
#colorscheme=beauty256
colorscheme=default
scrpt=${0##*/}  # script name

# Display usage if no parameters given
if [[ -z "$@" ]]; then
    echo " $scrpt <filename> - create HTML code from Vim syntax highlighting"
    exit
fi

# Syntax highlighting to HTML export
vim -f                                \
        +"syntax on"                  \
        +"set t_Co=256"               \
        +"set background=$background" \
        +"colorscheme $colorscheme"   \
        +"let html_use_css = 0"       \
        +"let html_no_pre = 1"        \
        +"let html_number_lines = 0"  \
        +"TOhtml"                     \
        +"x"                          \
        +"q" $filename

# Clean up HTML code
tidy -utf8 -f /dev/null --wrap -m $filename.html

# Delete the HTML meta page information.
sed -i '1,/body bgcolor=/d' $filename.html

# Remove line breaks (needed for some things like blog posts)
sed -i 's|<br>||g' $filename.html

# Remove the closing HTML tags
sed -i 's~</body[^>]*>~~g' $filename.html
sed -i 's~</html[^>]*>~~g' $filename.html

# Add preformatting tabs <pre> and </pre>
sed -i '1 i <pre>' $filename.html
sed -i '$ a </pre>' $filename.html

# Remove trailing blank lines
while [ "$(tail -n 1 $filename.html)" == "\n" ]; do
    sed -i '$d' $filename.html
done

# Delete newline of last <font> line for better formatting
sed -i ':a;N;$!ba;s/\(.*\)\n/\1/' $filename.html
sed -i ':a;N;$!ba;s/\(.*\)\n/\1/' $filename.html

# Delete final newline
perl -i -e 'local $/; $_ = <>; s/\n$//; print' $filename.html
