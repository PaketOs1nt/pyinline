# PyInline – Python AST inliner/cleaner
Simple python AST cleaner/inliner

## Requires python 3.9+

## How to use
### `python path/to/pyinline.py PATH/TO/TARGET.py PASS_COUNT`
### or
### `python path/to/pyinline.py PATH/TO/TARGET.py PASS_COUNT > output.py`

## Features:
- TypeCleaner - replaces `int(123)` -> `123` or `str(123)` -> `'123'`
- NoJunkConsts - just removes junk constants
- InlineOps - inlines simple expressions, `1 + 123` -> `124` or `'asd' + '_123'` -> `'asd_123'`
- NoStupidLambda - replaces expressions like `(lambda: 1)()` -> `1`
- NoJunkVars - removes unusable vars / classes / functions

## Example:
<img width="956" height="565" alt="изображение" src="https://github.com/user-attachments/assets/08101093-f6f0-4702-a3e3-9af8290864e6" />



