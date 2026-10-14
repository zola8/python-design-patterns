import copy
from contextlib import asynccontextmanager
from dataclasses import dataclass
from dataclasses import field

import uvicorn
from fastapi import FastAPI
from fastapi import HTTPException
from pydantic import BaseModel


# ==========================================
# ENEMY MODEL (simplified for brevity)
# ==========================================
@dataclass
class Enemy:
    name: str
    hp: int
    attack: int
    position: tuple[int, int]
    loot_table: list[str] = field(default_factory=list)
    abilities: list[str] = field(default_factory=list)


# ==========================================
# REGISTRY
# ==========================================
class EnemyRegistry:
    def __init__(self):
        self._prototypes: dict[str, Enemy] = {}

    def register(self, key: str, template: Enemy):
        self._prototypes[key] = template

    def spawn(self, key: str, position: tuple[int, int], **overrides) -> Enemy:
        if key not in self._prototypes:
            raise KeyError(f"Unknown enemy type: {key}")
        new_enemy = copy.deepcopy(self._prototypes[key])
        new_enemy.position = position
        for k, v in overrides.items():
            setattr(new_enemy, k, v)
        return new_enemy


bestiary = EnemyRegistry()


# ==========================================
# LIFESPAN (Modern startup/shutdown)
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP: Register enemy prototypes
    print("[Lifespan] Loading bestiary...")
    bestiary.register("goblin", Enemy(
        name="Goblin", hp=50, attack=8, position=(0, 0),
        loot_table=["gold_coin", "rusty_dagger"],
        abilities=["stab", "dodge"],
    ))
    bestiary.register("dragon", Enemy(
        name="Dragon", hp=500, attack=50, position=(0, 0),
        loot_table=["dragon_scale", "gold_pile"],
        abilities=["fire_breath", "fly"],
    ))
    print(f"[Lifespan] Loaded {len(bestiary._prototypes)} enemy types")

    yield  # App runs here

    print("[Lifespan] Shutting down...")


# ==========================================
# APP
# ==========================================
app = FastAPI(lifespan=lifespan)


class SpawnRequest(BaseModel):
    enemy_type: str
    position: tuple[int, int]
    overrides: dict = {}


@app.post("/spawn")
async def spawn_enemy(req: SpawnRequest):
    try:
        enemy = bestiary.spawn(
            req.enemy_type,
            position=req.position,
            **req.overrides
        )
        return {
            "name": enemy.name,
            "hp": enemy.hp,
            "position": enemy.position,
            "status": "spawned"
        }
    except KeyError as e:
        raise HTTPException(404, str(e))


@app.get("/bestiary")
async def list_bestiary():
    return {
        key: {"name": e.name, "hp": e.hp, "attack": e.attack}
        for key, e in bestiary._prototypes.items()
    }


if __name__ == '__main__':
    uvicorn.run(app, port=8080)
