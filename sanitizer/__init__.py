# Triggers collected from common prompt-injection demos
TRIGGERS = [
    r"(?i)ignore\s+(?:all|previous).*instruction",
    r"(?i)\byou\s+must\b",
    r"(?i)as an ai (?:language )?model",
    r"<!--.*?-->",                          # hidden HTML comments
    r"\\begin\{comment}.*?\\end\{comment}", # LaTeX comment env
]
