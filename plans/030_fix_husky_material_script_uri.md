# Fix Husky Material Script URI

Status: executed

## Date

2026-06-07

## Goal

Fix the Gazebo SDF warning about material `<script>` elements missing a child
`<uri>` element in `models/husky/model.sdf`.

## Planned Changes

- Add `file://media/materials/scripts/gazebo.material` as the `<uri>` child in
  every Husky visual material `<script>` block.
- Preserve the existing Gazebo material names: `Gazebo/FlatBlack`,
  `Gazebo/Yellow`, and `Gazebo/Grey`.
- Leave the DiffDrive plugin unchanged.

## Verification Plan

```bash
python3 -m xml.etree.ElementTree models/husky/model.sdf
rg -n "<script>|<uri>file://media/materials/scripts/gazebo.material</uri>|<name>Gazebo/" models/husky/model.sdf
```

## Execution Result

- Added the standard Gazebo material script URI to all Husky material script
  blocks.
- Verified the SDF parses as XML.
- Verified all nine material script blocks have the expected URI.

## Follow-Up Notes

Runtime verification still requires launching the world in Gazebo Sim and
confirming the warning is gone.
