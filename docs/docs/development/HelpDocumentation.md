# Help File Format


Some CSE UI components provide a markdown documentation to the user, such as the Text UI. That documentation is imported from the [init](https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/acme/init){target=_new} directory as well. The file extension for documentation files is `.docmd`. 

## Format

In the documentation file individual sections are separated by markdown level-1 headers where the header title is the help topic for the following section, which is markdown text with the acual help text.

## Examples


```markdown
# Topic 1

Some help text for topic 1 in markdown format.

## Help sub section that belongs to topic 1

Some help text for the sub section in markdown format.

# Topic 2

Another help text for topic 2 in markdown format.

...

```



