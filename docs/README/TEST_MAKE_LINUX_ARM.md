# TEST_MAKE_LINUX_ARM

## Purpose
Smoke-test `make-linux-arm.sh`: aarch64 graft, steam helper scripts (`launch-steam.sh`, `add-to-steam.sh`, `.desktop`), idempotent re-run. Uses `--no-archive` so tests stay fast.

## Usage
```bash
bash test/test_make_linux_arm.sh
```

## Related
- [MAKE_LINUX_ARM.md](MAKE_LINUX_ARM.md)
- [ADD_TO_STEAM.md](ADD_TO_STEAM.md)
