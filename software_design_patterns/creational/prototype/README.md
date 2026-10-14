# Prototype Pattern

The **Prototype Pattern** is about creating new objects by cloning existing ones,
rather than constructing them from scratch.

```python
# Spawning a single enemy — so much boilerplate!
goblin1 = Enemy(
    name="Goblin",
    hp=50, mana=10, attack=8, defense=3, speed=5,
    position=(10, 20),
    loot_table=["gold_coin", "rusty_dagger"],
    abilities=["stab", "dodge"],
    ai_behavior="aggressive",
    sprite="goblin.png",
    sound="goblin_laugh.wav"
)

# Need another goblin 5 tiles away? Repeat everything!
goblin2 = Enemy(
    name="Goblin",
    hp=50, mana=10, attack=8, defense=3, speed=5,
    position=(15, 20),  # Only this changed!
    loot_table=["gold_coin", "rusty_dagger"],
    abilities=["stab", "dodge"],
    ai_behavior="aggressive",
    sprite="goblin.png",
    sound="goblin_laugh.wav"
)
```

The Prototype pattern says: create a template object once, then clone it and modify only what's different.
