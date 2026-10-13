class Computer:
    def __init__(self):
        # We initialize with empty/default values
        self.cpu = "Standard CPU"
        self.ram = "8GB"
        self.storage = "256GB SSD"
        self.gpu = None
        self.has_cooling = False

    def __str__(self):
        specs = [f"CPU: {self.cpu}", f"RAM: {self.ram}", f"Storage: {self.storage}"]
        if self.gpu: specs.append(f"GPU: {self.gpu}")
        if self.has_cooling: specs.append("Liquid Cooling: Yes")
        return " | ".join(specs)


class ComputerBuilder:
    def __init__(self):
        self._computer = Computer()

    def set_cpu(self, cpu: str):
        self._computer.cpu = cpu
        return self

    def set_ram(self, ram: str):
        self._computer.ram = ram
        return self

    def add_gpu(self, gpu: str):
        self._computer.gpu = gpu
        return self

    def add_liquid_cooling(self):
        self._computer.has_cooling = True
        return self

    def build(self) -> Computer:
        # Best Practice: Put final validation here!
        if "Gaming" in self._computer.cpu and not self._computer.gpu:
            raise ValueError("A Gaming CPU requires a GPU!")
        return self._computer


if __name__ == '__main__':
    office_pc = (ComputerBuilder()
                 .set_cpu("Office i3")
                 .set_ram("16GB")
                 .build())

    print(office_pc)

    gaming_pc = (ComputerBuilder()
                 .set_cpu("Gaming i9")
                 .set_ram("64GB")
                 .add_gpu("RTX 4090")
                 .add_liquid_cooling()
                 .build())

    print(gaming_pc)
