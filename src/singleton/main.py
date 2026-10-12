from singleton.another_module.singleton_config import config
from singleton.singleton_lazy import LazySingleton

# Anywhere in your app, you just import 'config'.
# It's guaranteed to be the exact same instance.

if __name__ == '__main__':
    print(config.db_host)

    s1 = LazySingleton()
    s2 = LazySingleton()

    print(s1, s2, s1 == s2)
    s1.print_self()
