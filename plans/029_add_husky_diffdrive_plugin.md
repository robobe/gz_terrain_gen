# Add Husky DiffDrive Plugin

Status: executed

## Date

2026-06-07

## Goal

Add the Gazebo Sim DiffDrive plugin to `models/husky/model.sdf`.

## Planned Changes

- Replace the old commented Gazebo Classic Husky plugin block with the built-in
  Gazebo Sim `gz::sim::systems::DiffDrive` plugin.
- Configure the plugin with the four Husky wheel joints.
- Use wheel separation `0.5709`, wheel radius `0.17775`, and odometry publish
  frequency `50`.

## Verification Plan

```bash
python3 -m xml.etree.ElementTree models/husky/model.sdf
rg -n "husky_diff_controller|libhusky_gazebo_plugins|gz-sim-diff-drive-system|left_joint|right_joint|wheel_radius" models/husky/model.sdf
```

## Execution Result

- Replaced the old commented `libhusky_gazebo_plugins.so` block with a Gazebo
  Sim DiffDrive plugin block.
- Verified the SDF parses as XML.
- Verified the old Classic plugin identifiers are absent and the new DiffDrive
  plugin fields are present.

## Follow-Up Notes

Runtime movement should be verified in Gazebo Sim by publishing
`gz.msgs.Twist` messages to `/model/husky/cmd_vel`.
