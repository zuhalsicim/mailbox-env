# mailbox-env

A generator that writes the mailbox of an invented company from hidden process graphs.
Each generated instance is a task folder: an agent has to find the processes in the mail.
A grader checks the agent's answer against the truth the generator knows.

```sh
uv sync
uv run python -m mailgen generate --level 2 --seed 7 --out tasks
uv run python -m mailgen audit --n 300
uv run pytest
```
