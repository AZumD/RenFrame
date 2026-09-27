# ELF.md

Equivalent script: `renframe/elf.py`

## Purpose

Identify Linux shared-object architecture by parsing ELF headers in pure Python.

## API

- `read_elf_architecture(path) -> str | None`
- `is_elf_file(path) -> bool`

## Machines mapped

`x86`, `x86_64`, `arm`, `aarch64`, plus a few others; unknown `e_machine` values return `unknown(<id>)`.
