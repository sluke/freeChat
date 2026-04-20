# Example Skill for FreeChat

This is an example skill demonstrating the FreeChat skill system.

## Installation

```bash
/skill install /path/to/example_skill
```

## Tools Provided

### example_hello
Returns a greeting message.

Parameters:
- `name` (string, required): Name to greet

Example:
```
> /tool call example_hello name="World"
Hello, World!
```

### example_count
Count words in a text.

Parameters:
- `text` (string, required): Text to count words in

## Development

To create your own skill:

1. Create a new directory with `skill.toml`
2. Define your tools and their parameters
3. Implement the tool handlers
4. Install with `/skill install <path>`

See the FreeChat documentation for more details.
