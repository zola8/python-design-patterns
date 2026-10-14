import copy

from creational.prototype.example_deepcopy import DRAGON_TEMPLATE
from creational.prototype.example_deepcopy import Enemy
from creational.prototype.example_deepcopy import GOBLIN_TEMPLATE


class EnemyRegistry:
    """A registry of enemy prototypes — like a game's bestiary."""

    def __init__(self):
        self._prototypes: dict[str, Enemy] = {}

    def register(self, key: str, template: Enemy):
        """Register a new prototype."""
        self._prototypes[key] = template

    def spawn(self, key: str, position: tuple[int, int], **overrides) -> Enemy:
        """Clone and spawn an enemy by its registry key."""
        if key not in self._prototypes:
            raise KeyError(f"Unknown enemy type: {key}")

        new_enemy = copy.deepcopy(self._prototypes[key])
        new_enemy.position = position

        for k, v in overrides.items():
            setattr(new_enemy, k, v)

        return new_enemy

    def list_types(self) -> list[str]:
        return list(self._prototypes.keys())


# ==========================================
# USAGE
# ==========================================
if __name__ == '__main__':
    bestiary = EnemyRegistry()

    # Register templates at game startup
    bestiary.register("goblin", GOBLIN_TEMPLATE)
    bestiary.register("dragon", DRAGON_TEMPLATE)
    bestiary.register("orc", Enemy(
        name="Orc", hp=100, mana=20, attack=15, defense=10, speed=4,
        position=(0, 0), loot_table=["axe", "gold_coin"],
        abilities=["smash"], ai_behavior="aggressive"
    ))

    # Spawn enemies anywhere in the game
    goblin = bestiary.spawn("goblin", position=(5, 10))
    orc = bestiary.spawn("orc", position=(8, 12), hp=150, name="Orc Warlord")
    dragon = bestiary.spawn("dragon", position=(100, 100))

    print(f"Available enemy types: {bestiary.list_types()}")
    orc.display()  # [Orc Warlord] HP:150 ATK:15 at (8, 12)
