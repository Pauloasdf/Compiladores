__symtable = {}
case_insensitive_symtable = False  # pylint: disable=invalid-name


class SymbolRedefinitionError(Exception):
    """Error raised when a symbol is already defined."""

    def __init__(self, symbol, lineno, original=None):
        """Initialize error with proper message."""
        super().__init__(
            f"Redeclaration of symbol "
            f"'{original if original else symbol['name']}':{lineno}:"
            f"original declaration at line {symbol['lineno']}"
        )


class InternalError(Exception):
    """Error raised when a symbol is already defined."""

    def __init__(self, msg):
        """Initialize error with proper message."""
        super().__init__(f"Internal error: {msg}")


def __tr_symbol(symbol):
    return symbol.upper() if case_insensitive_symtable else symbol, symbol


def add_symbol(symbol, sym_type, **kwargs):
    """Create new symbol in the symbol table."""
    symbol, original = __tr_symbol(symbol)

    obj = __symtable.get(symbol)
    if obj:
        lineno = symbol.get("lineno")
        if lineno >= 0:
            raise SymbolRedefinitionError(obj, lineno, original)
        obj.update(kwargs)
    else:
        kwargs["name"] = symbol
        kwargs["type"] = sym_type
        __symtable[symbol] = kwargs


def set_symbol(symbol, **kwargs):
    """Set values of a symbol in symbol table."""
    symbol, original = __tr_symbol(symbol)
    obj = __symtable.get(symbol)
    if obj is None:
        raise InternalError(f"Symbol not defined: {original}")
    if "name" in kwargs:
        raise InternalError(
            f"Cannot modify symbol '{original}' attribute 'name'."
        )
    if "lineno" in kwargs and not obj.get("lineno", -1) < 0:
        raise InternalError(
            f"Cannot modify symbol {original} attribute 'line'."
        )
    obj.update(kwargs)


def get_symbol(symbol):
    """Retrieve symbol from symbol table."""
    return __symtable.get(__tr_symbol(symbol)[0])


def get_symbols_by_class(symtype):
    """Retrieve all symbols with a given type from symbol table."""
    return {k: v for k, v in __symtable.items() if v["type"] == symtype}


def remove_symbol(symbol):
    """Remove symbol from symbol table."""
    symbol, original = __tr_symbol(symbol)
    if symbol in __symtable:
        del __symtable[symbol]
    else:
        raise InternalError(f"Symbol not defined: {original}")


def increment_symbol_usage(symbol, lineno, amount=1):
    """Increment symbol attribute 'usage' by the given amount."""
    sym = get_symbol(symbol)
    if sym is None:
        raise Exception(f"Unknown symbol:{lineno}:'{symbol}'")
    usage = sym.get("usage", 0) + amount
    set_symbol(symbol, usage=usage)
