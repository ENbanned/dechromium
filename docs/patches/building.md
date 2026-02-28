# Building from Source

## Requirements

| Resource | Minimum | Recommended |
|---|---|---|
| OS | Ubuntu 22.04 / Debian 12 | Ubuntu 24.04 |
| RAM | 16 GB | 32+ GB |
| Disk | 100 GB free | 150+ GB |
| CPU | 4 cores | 16+ cores |

First build takes 2-4 hours. Incremental builds after patch changes take 2-5 minutes.

## 1. Install depot_tools
```bash
cd /opt
git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git
echo 'export PATH="/opt/depot_tools:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## 2. Fetch Chromium
```bash
mkdir -p ~/chromium && cd ~/chromium
fetch --nohooks chromium
cd src
git fetch --tags
git checkout 145.0.7632.116
gclient sync --with_branch_heads --with_tags
./build/install-build-deps.sh
gclient runhooks
```

This downloads ~30 GB.

## 3. Configure
```bash
mkdir -p out/Release
cat > out/Release/args.gn << 'GN'
is_official_build = true
is_chrome_branded = false
proprietary_codecs = true
ffmpeg_branding = "Chrome"
is_debug = false
symbol_level = 0
blink_symbol_level = 0
v8_symbol_level = 0
enable_nacl = false
is_component_build = false
GN

gn gen out/Release
```

## 4. Apply patches
```bash
export CHROMIUM_SRC="$PWD"
/path/to/dechromium/build/apply_patches.sh 145.0.7632.116
```

This creates a git branch `aspect` with one commit per patch. You can inspect any patch:
```bash
git log --oneline 145.0.7632.116..aspect
git show HEAD~3  # view a specific patch
```

## 5. Build
```bash
/path/to/dechromium/build/build.sh
# or directly:
autoninja -C out/Release chrome -j$(nproc)
```

The binary is at `out/Release/chrome`.

## 6. Install

Copy the binary to the versioned directory:
```bash
VERSION=145.0.7632.116
mkdir -p ~/.dechromium/browsers/$VERSION
cp out/Release/chrome ~/.dechromium/browsers/$VERSION/chrome
```

The library auto-detects the latest installed version from `~/.dechromium/browsers/`.

## Working with patches

**Add a new patch:**
```bash
cd $CHROMIUM_SRC
# make your changes
./path/to/dechromium/build/new_patch.sh 012-my-feature
./path/to/dechromium/build/export_patches.sh
```

**Edit an existing patch:**
```bash
./path/to/dechromium/build/edit_patch.sh
# mark the commit as 'edit' in the interactive rebase
# make changes
git add -A && git commit --amend --no-verify
git rebase --continue
./path/to/dechromium/build/export_patches.sh
```

**Rebuild from patches (clean slate):**
```bash
./path/to/dechromium/build/apply_patches.sh 145.0.7632.116
./path/to/dechromium/build/build.sh
```
