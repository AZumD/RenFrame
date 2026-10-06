# RenFrame Overview

RenFrame turns Ren'Py desktop builds into native Linux ARM64 packages for Steam Frame.

Primary path (0.1.0): **GUI / `renpy_arm` convert** — download matching `sdkarm`, graft `py*-linux-aarch64`, write Steam helpers, emit a zip.

Secondary: **`renframe inspect` / `renframe build`** — compatibility reports and runtime-directory swap when you already have an ARM Ren'Py tree.

See [docs/README/OVERVIEW.md](README/OVERVIEW.md).
