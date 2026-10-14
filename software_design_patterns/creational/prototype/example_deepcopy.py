import copy
from dataclasses import dataclass
from dataclasses import field


@dataclass
class Enemy:
    name: str
    hp: int
    mana: int
    attack: int
    defense: int
    speed: int
    position: tuple[int, int]
    loot_table: list[str] = field(default_factory=list)
    abilities: list[str] = field(default_factory=list)
    ai_behavior: str = "passive"
    sprite: str = ""
    sound: str = ""

    def display(self):
        print(f"[{self.name}] HP:{self.hp} ATK:{self.attack} at {self.position}")


# ==========================================
# 1. CREATE TEMPLATES (Prototypes)
# ==========================================
GOBLIN_TEMPLATE = Enemy(
    name="Goblin",
    hp=50, mana=10, attack=8, defense=3, speed=5,
    position=(0, 0),  # Will be overridden
    loot_table=["gold_coin", "rusty_dagger"],
    abilities=["stab", "dodge"],
    ai_behavior="aggressive",
    sprite="goblin.png",
    sound="goblin_laugh.wav"
)

DRAGON_TEMPLATE = Enemy(
    name="Dragon",
    hp=500, mana=200, attack=50, defense=30, speed=10,
    position=(0, 0),
    loot_table=["dragon_scale", "gold_pile", "magic_gem"],
    abilities=["fire_breath", "tail_swipe", "fly"],
    ai_behavior="territorial",
    sprite="dragon.png",
    sound="dragon_roar.wav"
)


# ==========================================
# 2. CLONE AND CUSTOMIZE
# ==========================================
def spawn_enemy(template: Enemy, position: tuple[int, int], **overrides) -> Enemy:
    """Clone a template enemy and customize it."""
    # CRITICAL: Use deepcopy to avoid shared mutable references!
    new_enemy = copy.deepcopy(template)
    new_enemy.position = position

    # Apply any overrides
    for key, value in overrides.items():
        setattr(new_enemy, key, value)

    return new_enemy


# ==========================================
# 3. USAGE — Spawn an entire horde!
# ==========================================
if __name__ == "__main__":
    # Spawn 3 goblins at different positions
    goblin1 = spawn_enemy(GOBLIN_TEMPLATE, position=(10, 20))
    goblin2 = spawn_enemy(GOBLIN_TEMPLATE, position=(15, 20))
    goblin3 = spawn_enemy(GOBLIN_TEMPLATE, position=(20, 20), hp=80, name="Goblin Chief")

    # Spawn a dragon
    dragon = spawn_enemy(DRAGON_TEMPLATE, position=(50, 50))

    # Display them
    goblin1.display()
    goblin2.display()
    goblin3.display()
    dragon.display()

    # Prove they're independent (not sharing references!)
    goblin1.loot_table.append("magic_ring")
    print(f"\nGoblin 1 loot: {goblin1.loot_table}")
    print(f"Goblin 2 loot: {goblin2.loot_table}")  # Unchanged!
    print(f"Template loot: {GOBLIN_TEMPLATE.loot_table}")  # Unchanged!
