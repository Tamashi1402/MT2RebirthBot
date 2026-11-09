_MOVEMENT_VKS = (0x57, 0x41, 0x53, 0x44)


def stop_kraken_dodge(wait: bool = True, timeout: float = 2.5):
    """Release movement keys left over from older dodge workers."""
    vks = list(_MOVEMENT_VKS)
    try:
        from macro_runner import remapped_movement_vks
        vks = list(dict.fromkeys(vks + remapped_movement_vks()))
    except Exception:
        pass
    try:
        from macro_runner import _key_up
        for vk in vks:
            try:
                _key_up(vk)
            except Exception:
                pass
    except Exception:
        pass
