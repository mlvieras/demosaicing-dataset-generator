import sys

'''
    Prints all params joined by a space inline.

    Parameters:
        - *text: captures all passed parameters. Must be strings.
'''
def print_inline(*text):
  sys.stdout.write(' '.join(text) + 50 * ' ' + '\r')
  sys.stdout.flush()
