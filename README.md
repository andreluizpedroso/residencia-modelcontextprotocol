# Estudo-MCP — Model Context Protocol na prática

![Sprint](https://img.shields.io/badge/Sprint-8%2F8-success)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![MCP SDK](https://img.shields.io/badge/MCP-python--sdk-000000)

Estudo guiado do **Model Context Protocol (MCP)**, do zero, em formato de sprints. Cada sprint tem objetivo, conceitos ensinados, exercício prático, perguntas de validação e code review, registrados em `docs/sprints/`.

Referência oficial: [github.com/modelcontextprotocol](https://github.com/modelcontextprotocol)

---

## Progresso das Sprints

| Sprint | Tema | Status |
|--------|------|--------|
| 1 | Fundamentos do MCP + setup do ambiente | ✅ Concluída |
| 2 | Primeiro MCP Server — Tools | ✅ Concluída |
| 3 | Resources & Prompts | ✅ Concluída |
| 4 | Testando com MCP Inspector | ✅ Concluída |
| 5 | Client MCP customizado + conexão com um Host real | ✅ Concluída |
| 6 | Sampling & Roots | ✅ Concluída |
| 7 | Transporte remoto (HTTP) & Autenticação | ✅ Concluída |
| 8 | Projeto final — server MCP para um caso de uso real | ✅ Concluída |

---

## Estrutura

```
MCP/
├── README.md
├── docs/
│   └── sprints/                      # registro detalhado de cada sprint
│       ├── sprint-01.md
│       ├── sprint-02.md
│       └── ...
└── servers/                           # código dos servers MCP construídos nos exercícios
    ├── sprint-01-hello-mcp/
    ├── sprint-02-tools-server/
    ├── sprint-03-resources-prompts/
    ├── sprint-05-custom-client/
    ├── sprint-06-sampling-roots/
    ├── sprint-07-http-auth/
    └── sprint-08-final-project/
```

Cada pasta em `servers/` é um projeto `uv` independente (próprio `pyproject.toml`/`.venv`), criado sob demanda conforme a sprint correspondente introduz uma dependência ou conceito novo.
