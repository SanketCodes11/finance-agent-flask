import os
import re

file_path = 'app/templates/stock_detail.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("    });\n    }\n    \n    document.getElementById('bd-theme')", "    });\n    \n    document.getElementById('bd-theme')")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
