import importlib.metadata

import mcp


def main() -> None:
    version = importlib.metadata.version("mcp")
    print(f"SDK oficial do MCP (python) instalado com sucesso — versao {version}")
    print(f"Modulo importado de: {mcp.__file__}")


if __name__ == "__main__":
    main()
