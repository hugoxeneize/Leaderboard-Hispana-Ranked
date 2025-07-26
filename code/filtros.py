USUARIOS_EXCLUIDOS = [
    "DARVY__X1", "messi", "infume", 
]

lacabra = ["hugoxeneize", "xeneizee"]

def filtrar_usuarios(df, columna_nick="Nickname", excluidos=USUARIOS_EXCLUIDOS):
    """
    Filtra los usuarios excluidos de la lista."""
    return df[~df[columna_nick].str.lower().isin([u.lower() for u in excluidos])].reset_index(drop=True)

def poner_cabra(df, columna_nick="Nickname", lacabra=lacabra):
    """    """
    def agregar_cabra(nick):
        if str(nick).lower() in [u.lower() for u in lacabra]:
            return f"{nick} 🐐"
        return nick
    df[columna_nick] = df[columna_nick].apply(agregar_cabra)
    return df