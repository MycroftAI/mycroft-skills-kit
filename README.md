# Mycroft Skills Kit

*Mycroft Skills Kit*

[![msk-create](https://images2.imgbox.com/ab/25/6kbqKbXh_o.gif)](https://asciinema.org/a/X5pWLPOpsMLUPYp5kgswNm5Zu?speed=1.5)

A tool to help with creating, uploading, and upgrading Mycroft skills on the
[skills repo](https://github.com/mycroftai/mycroft-skills).

## Features

 - Create a new skill
 - Create an intent test for a skill
 - Upload a skill
 - Upgrade an existing skill

## Install

*Note: Only Linux has been tested*

```bash
pip3 install msk
```

## Usage

```bash
msk create
msk create-test /opt/mycroft/skills/myskill
msk submit /opt/mycroft/skills/myskill
```
### Creating a New Skill

`msk create`:

[![msk-create](https://images2.imgbox.com/ab/25/6kbqKbXh_o.gif)](https://asciinema.org/a/X5pWLPOpsMLUPYp5kgswNm5Zu?speed=1.5)

### Creating Tests

`msk create-test /opt/mycroft/skills/myskill`:

[![msk-create-test](https://images2.imgbox.com/9c/c8/gLRS7xuL_o.gif)](https://asciinema.org/a/Ayzaj6QJbKGBfs2eIQWr11idH?speed=1.5)

## Submitting a new skill / Updating existing skill

`msk submit /opt/mycroft/skills/myskill`:

[![msk-submit](https://images2.imgbox.com/7a/5f/RcBxgLXc_o.gif)](https://asciinema.org/a/242108)

 --or--

```bash
cd /opt/mycroft/skills/myskill
msk submit .
```
