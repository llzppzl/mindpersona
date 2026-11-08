"""Read an MCP result field by its protocol name (isError, inputSchema, serverInfo) on mcp 1.x and 2.x.

mcp 2.x renamed the Python attributes to snake_case (is_error, input_schema, server_info); both
versions still dump them under the protocol's camelCase names."""


def field(model, name: str):
    return model.model_dump(by_alias=True)[name]
