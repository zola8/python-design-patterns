class _Config:
    """Internal class, meant to be instantiated only once."""

    def __init__(self):
        self.db_host = "localhost"
        self.db_port = 5432
        print("Config initialized eagerly!")


# Eagerly create the single instance at the module level
# modules are singletons by default

config = _Config()
