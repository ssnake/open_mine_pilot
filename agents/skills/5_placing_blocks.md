5. Placing Blocks
- To place a block (like a crafting table), first ensure you have the block in your inventory.
- Call `equip_item` with `destination="hand"` to hold the block you want to place.
- Identify a solid reference block nearby (e.g. using `get_voxel_map` or finding the block under your feet `y-1`).
- Ensure you do not place the block inside your own body! If you place a block at your own coordinates (`~ ~ ~`), it may fail. You must target a block next to you or below you, and ensure the resulting placed block coordinates are not your exact feet or head position unless you intend to jump.
- Call `async_place_block` with the reference block's coordinates and the face direction (e.g., `face_y=1` to place it on top of the reference block). Wait for `[SYSTEM EVENT: placementCompleted]`.
