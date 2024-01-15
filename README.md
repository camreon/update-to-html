# eml-to-html

Tiny CLI tool that batch converts `.eml` email files to `.html` files to create a navigable website.

## Installation
Install python
Run `pip install -r requirements.txt` to install dependencies

## Usage
```
eml-to-html [OUTPUT PATH] [EML FILE]...
```

Feel free to pass a _glob_. For example:

```
eml-to-html some_email_file_1.eml some_email_file_2.eml
```

and

```
eml-to-html *.eml
```

are both valid calls to the command. Cheers!

✨

## Example

Running `eml-to-html` on the [`test_emails`](https://github.com/dunnkers/eml-to-html/tree/master/test_emails) folder:

```
$ eml-to-html test_emails/*.eml
🟢 Written `test_email_1.html`
🟢 Written `test_email_2.html`
```

File tree is now:

```
$ tree test_emails 
test_emails
├── test_email_1.eml
├── test_email_1.html
├── test_email_2.eml
└── test_email_2.html

0 directories, 4 files
```

## About
This module was based on [Jeroen Overschie's](https://jeroenoverschie.nl/) in 2022.