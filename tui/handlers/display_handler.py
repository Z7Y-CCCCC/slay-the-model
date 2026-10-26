# -*- coding: utf-8 -*-
"""
Display handler - manages content for the display panel.
Handles player info, map view, combat view, and room-specific displays.
"""
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from engine.game_state import GameState
    from engine.combat import Combat
    from rooms.base import Room


def _resolve_text(value, field: str, fallback: str = "") -> str:
    """Resolve localizable fields without making the renderer depend on a full model object."""
    try:
        resolved = value.local(field) if hasattr(value, "local") else getattr(value, field, fallback)
        if hasattr(resolved, "resolve"):
            resolved = resolved.resolve()
        return str(resolved) if resolved is not None else fallback
    except (AttributeError, KeyError, TypeError):
        return fallback


class DisplayHandler:
    """Handles display panel content generation."""
    
    def __init__(self, app):
        self._app = app
    
    def update_player_info(self, gs: 'GameState'):
        """Update player info section."""
        self._app.update_player_info(gs.player, gs)
    
    def display_map(self, gs: 'GameState'):
        """Display map for node selection."""
        from localization import t
        
        lines = []
        lines.append(t("ui.map_title", default="[ MAP ]"))
        lines.append("─" * 38)
        
        def _colorize_map(raw_text: str) -> str:
            emoji_map = {
                "M": ("[#50afff]👾[/]", "[#1a2a3a]👾[/]"),      # (亮色, 暗色)
                "E": ("[#ff5555]👹[/]", "[#3a1a1a]👹[/]"),
                "$": ("[#ffd700]⚖️[/]", "[#3a321a]⚖️[/]"),
                "?": ("[#bd93f9]🎭[/]", "[#2a1a3a]🎭[/]"),
                "R": ("[#ff8c00]🔥[/]", "[#3a221a]🔥[/]"),
                "T": ("[#00ffff]💎[/]", "[#1a3a3a]💎[/]"),
                "B": ("[bold #ffd700]👑[/]", "[#3a321a]👑[/]"),
                "N": ("[#00e676]🌟[/]", "[#1a3a22]🌟[/]"),
            }
            
            output_lines = []
            for line in raw_text.splitlines():
                if ("Floor" in line or "层" in line) and ": " in line:
                    parts = line.split(": ", 1)
                    floor_prefix = parts[0]
                    nodes_part = parts[1]
                    
                    new_nodes = []
                    i = 0
                    while i < len(nodes_part):
                        node_str = nodes_part[i:i+5]
                        if len(node_str) == 5 and node_str.startswith("[") and node_str.endswith("]"):
                            status = node_str[1]
                            room_type_char = node_str[2]
                            
                            colors = emoji_map.get(room_type_char, (room_type_char, room_type_char))
                            
                            if status == "*":
                                formatted = f"[bold #ff55ff blink]▶[/]{colors[0]}[bold #ff55ff blink]◀[/]"
                            elif status == ">":
                                formatted = f"[bold #00e676]▶[/]{colors[0]}[bold #00e676]◀[/]"
                            elif status == "^":
                                formatted = f"[dim]✔[/]{colors[1]}"
                            else:
                                formatted = f"[#44475a]\[[/#44475a]{colors[1]}[#44475a]\][/#44475a]"
                            new_nodes.append(formatted)
                        else:
                            new_nodes.append(node_str)
                        i += 5
                    
                    output_lines.append(f"[bold #bd93f9]{floor_prefix}:[/]  {' '.join(new_nodes)}")
                elif any(c in line for c in ("/", "|", "\\")):
                    conn_line = line.replace("/", "[#44475a]/[/]").replace("|", "[#44475a]|[/]").replace("\\", "[#44475a]\\\\[/#44475a]")
                    output_lines.append(conn_line)
                else:
                    escaped_line = line.replace("[", "\[").replace("]", "\]")
                    # Map legend symbol colorization
                    escaped_line = escaped_line.replace("\[M\]", "\[[#50afff]👾[/]普通怪\]")
                    escaped_line = escaped_line.replace("\[E\]", "\[[#ff5555]👹[/]精英怪\]")
                    escaped_line = escaped_line.replace("\[$\]", "\[[#ffd700]⚖️[/]商店商贩\]")
                    escaped_line = escaped_line.replace("\[?\]", "\[[#bd93f9]🎭[/]未知事件\]")
                    escaped_line = escaped_line.replace("\[R\]", "\[[#ff8c00]🔥[/]休息营火\]")
                    escaped_line = escaped_line.replace("\[T\]", "\[[#00ffff]💎[/]宝箱奖励\]")
                    escaped_line = escaped_line.replace("\[B\]", "\[[bold #ffd700]👑[/]幕后首领\]")
                    escaped_line = escaped_line.replace("\[N\]", "\[[#00e676]🌟[/]涅奥馈赠\]")
                    output_lines.append(escaped_line)
            return "\n".join(output_lines)

        if hasattr(gs, 'map_manager') and gs.map_manager:
            lines.append(_colorize_map(gs.map_manager.get_map_text_for_human()))
        else:
            lines.append(t("ui.no_map", default="No map available."))
        
        self._app.update_display_content("\n".join(lines))
    
    def display_combat(self, combat: 'Combat', gs: 'GameState'):
        """Display combat state."""
        import random
        from localization import t
        player = gs.player
        hand = player.card_manager.get_pile("hand")
        draw_pile = list(player.card_manager.get_pile("draw_pile"))
        discard_pile = list(player.card_manager.get_pile("discard_pile"))
        relics = list(getattr(player, "relics", []) or [])
        powers = list(getattr(player, "powers", []) or [])
        potions = list(getattr(player, "potions", []) or [])
        
        # Check for Frozen Eye relic
        has_frozen_eye = any(
            getattr(relic, "idstr", None) == "FrozenEye"
            for relic in relics
        )
        
        lines = []
        
        lines.append(f"[bold #d66a45]╔═ {t('combat.title', default='COMBAT')} ═╗[/bold #d66a45]")
        lines.append("─" * 38)

        # Keep the high-value tactical context above the art and card list.
        turn = getattr(getattr(combat, "combat_state", None), "combat_turn", 0)
        lines.append(
            f"[bold #d8b26e]TURN {turn}[/]  "
            f"[dim]Challenge tokens: {getattr(gs, 'challenge_tokens', 0)}[/]"
        )
        challenge = getattr(combat, "challenge", None)
        if challenge:
            lines.append(
                f"[bold #e59b4a]◆ {challenge.get('title', 'Challenge')}[/] "
                f"[dim]{challenge.get('description', '')}[/]"
            )
        affix = getattr(combat, "elite_mutation", None)
        if affix:
            lines.append(
                f"[bold #a78bba]◇ {affix.name}[/] [dim]{affix.description}[/]"
            )
        last_summary = getattr(combat, "turn_summary_history", None)
        if last_summary:
            lines.append(f"[dim]↳ {last_summary[-1]}[/]")
        
        lines.append("")
        lines.append(f"[bold #ff5555]⚔️  {t('combat.enemies', default='Enemies:')}[/bold #ff5555]")
        def _get_enemy_ascii(enemy_cls: str) -> str:
            cls_lower = enemy_cls.lower()
            if "slime" in cls_lower:
                return (
                    "   [#00e676]  .-----.  [/]\n"
                    "   [#00e676] /  ^  ^  \\ [/]\n"
                    "   [#00e676]|  [#ffffff]O   O[/]  |[/]\n"
                    "   [#00e676]|   \\___/  |[/]\n"
                    "   [#00e676] \\________/[/]"
                )
            elif "worm" in cls_lower:
                return (
                    "   [#ff9100]   /\\\\-/\    [/]\n"
                    "   [#ff9100]  /  . . \\   [/]\n"
                    "   [#ff1744] |  V V V |  [/]\n"
                    "   [#ff1744]  \\ A A A /  [/]\n"
                    "   [#ff9100]   \\_____/   [/]"
                )
            elif "cultist" in cls_lower:
                return (
                    "   [#ffd700]    _/\_     [/]\n"
                    "   [#ffd700]   ( >.< )   [/]\n"
                    "   [#ffd700]   /====\\    [/]\n"
                    "   [#ffd700]  / |||| \\   [/]\n"
                    "   [#ffd700]   \\_/\/_/   [/]"
                )
            elif "hexaghost" in cls_lower:
                return (
                    "   [#d500f9]     /\\     [/]\n"
                    "   [#d500f9]   / 🌟 \\   [/]\n"
                    "   [#d500f9] /\\  🔥  /\\ [/]\n"
                    "   [#d500f9] \\/  🔥  \\/ [/]\n"
                    "   [#d500f9]   \\ 🌟 /   [/]"
                )
            elif "sentry" in cls_lower:
                return (
                    "   [#00e5ff]    .---.    [/]\n"
                    "   [#00e5ff]   /|[■]|\\   [/]\n"
                    "   [#00e5ff]   |  |  |   [/]\n"
                    "   [#00e5ff]   \\  |  /   [/]\n"
                    "   [#00e5ff]    '---'    [/]"
                )
            elif "lagavulin" in cls_lower:
                return (
                    "   [#ffd700]    .---.    [/]\n"
                    "   [#ffd700]   /_____\\   [/]\n"
                    "   [#ffd700]  | [#ff0000][◎][/] |  [/]\n"
                    "   [#ffd700]   \\  =  /   [/]\n"
                    "   [#ffd700]   //   \\\\   [/]"
                )
            elif "nob" in cls_lower:
                return (
                    "   [#ff1744]    (\_/)    [/]\n"
                    "   [#ff1744]   ( 皿 )   [/]\n"
                    "   [#ff1744]   /|🪓|\\   [/]\n"
                    "   [#ff1744]  / |  | \\  [/]\n"
                    "   [#ff1744]   /_/\\_\\   [/]"
                )
            else:
                return (
                    "     [#a0a0a0]  (\\_/)   [/]\n"
                    "     [#a0a0a0] ( •.• )  [/]\n"
                    "     [#a0a0a0] /|   |\\  [/]\n"
                    "     [#a0a0a0]/ |   | \\ [/]\n"
                    "     [#a0a0a0]  /_/\\_\\  [/]"
                )

        for enemy in combat.enemies:
            if not enemy.is_dead():
                hp_ratio = enemy.hp / enemy.max_hp if enemy.max_hp > 0 else 0
                hp_color = "#00e676" if hp_ratio > 0.5 else ("#ff9100" if hp_ratio > 0.25 else "#ff1744")
                
                # Visual HP mini-bar
                bar_width = 10
                filled_len = int(hp_ratio * bar_width)
                empty_len = bar_width - filled_len
                mini_bar = f"[{hp_color}]{'█' * filled_len}[/][#333333]{'░' * empty_len}[/]"
                
                hp_str = f"HP: [{hp_color}]{enemy.hp}/{enemy.max_hp}[/] {mini_bar}"
                block_str = f" [bold #00e5ff](🛡️ {enemy.block})[/]" if enemy.block > 0 else ""
                
                intention_str = ""
                if enemy.current_intention:
                    intent_desc = enemy.current_intention.description
                    intent_key = f"{enemy.current_intention.name} {intent_desc}".lower()
                    
                    intent_icon = ""
                    intent_color = "white"
                    if any(token in intent_key for token in ("attack", "strike", "stab", "bash", "slam", "bite", "tackle", "damage")):
                        intent_icon = " ⚔️"
                        intent_color = "#ff1744"
                    elif any(token in intent_key for token in ("defend", "block", "guard")):
                        intent_icon = " 🛡️"
                        intent_color = "#00e5ff"
                    elif any(token in intent_key for token in ("debuff", "weak", "frail", "vulnerable", "poison")):
                        intent_icon = " 🧪"
                        intent_color = "#d500f9"
                    elif any(token in intent_key for token in ("buff", "ritual", "strength", "enrage", "gain")):
                        intent_icon = " ✨"
                        intent_color = "#ffd700"
                    
                    intention_str = f" [{intent_color}]{enemy.current_intention.description}{intent_icon}[/]"
                
                # Use localized enemy name
                enemy_name = enemy.local("name").resolve() if hasattr(enemy, 'local') else enemy.name
                
                enemy_icon = "👾"
                if "boss" in enemy.__class__.__name__.lower() or "heart" in enemy.__class__.__name__.lower():
                    enemy_icon = "👑"
                elif "elite" in enemy.__class__.__name__.lower():
                    enemy_icon = "👹"
                
                # Display enemy powers
                powers_list = []
                if hasattr(enemy, 'powers') and enemy.powers:
                    for power in enemy.powers:
                        power_name = power.local("name").resolve() if hasattr(power, 'local') else power.name
                        power_amount = power.amount if power.amount is not None and power.amount > 0 else None
                        if power_amount is not None:
                            powers_list.append(f"{power_name}x{power_amount}")
                        else:
                            powers_list.append(f"{power_name}")
                
                powers_str = f" [dim]Buffs: {', '.join(powers_list)}[/]" if powers_list else ""
                
                # Side-by-side Table.grid layout for enemy ASCII and details
                from rich.table import Table
                enemy_grid = Table.grid(expand=True, padding=(0, 2))
                enemy_grid.add_column("ascii", width=16, justify="center")
                enemy_grid.add_column("details")
                
                ascii_text = _get_enemy_ascii(enemy.__class__.__name__)
                details_text = (
                    f"{enemy_icon} [bold #ff8888]{enemy_name}[/] ── {intention_str}\n"
                    f"{hp_str}{block_str}\n"
                    f"{powers_str}"
                )
                
                enemy_grid.add_row(ascii_text, details_text)
                
                lines.append(enemy_grid)
                lines.append("")
        
        # Survival warnings
        incoming_damage = 0
        if hasattr(combat, "_estimate_incoming_damage"):
            try:
                incoming_damage = int(combat._estimate_incoming_damage())
            except Exception:
                incoming_damage = 0
        if incoming_damage > 0:
            if incoming_damage >= player.hp + player.block:
                lines.append(f"\n  [bold blink #ff1744]🚨 警告：本回合即将受到致命伤害 ~{incoming_damage} 点 (生命值 {player.hp} + 护甲 {player.block})！[/]")
            else:
                lines.append(f"\n  [bold #ff9100]⚠️ 预警：本回合即将受到伤害 ~{incoming_damage} 点，当前护甲 {player.block}。[/]")
        
        lines.append("")
        lines.append(f"[bold #00e5ff]🎴 {t('combat.hand', default='Hand:')}[/bold #00e5ff]")
        for i, card in enumerate(hand):
            # Get cost display
            cost = getattr(card, "cost", None)
            if cost is not None:
                if cost == -1:  # COST_X
                    cost_str = "[bold #ffffff](X)[/]"
                elif cost == -2:  # COST_UNPLAYABLE
                    cost_str = "[bold #999999](#)[/]"
                else:
                    cost_str = f"[bold #ffffff]({cost})[/]"
            else:
                cost_str = ""
            
            # Get card display name
            card_name = card.display_name.resolve() if hasattr(card, 'display_name') else card.__class__.__name__
            
            # Get card type and rarity
            card_type = getattr(card, "card_type", None)
            type_str = card_type.value if card_type and hasattr(card_type, 'value') else ""
            rarity = getattr(card, "rarity", "COMMON")
            rarity_name = str(rarity).upper()
            
            # Rarity styles
            rarity_stars = ""
            rarity_color = "white"
            if rarity_name == "RARE":
                rarity_stars = " 🌟"
                rarity_color = "#ffd700"  # Gold
            elif rarity_name == "UNCOMMON":
                rarity_stars = " ⭐"
                rarity_color = "#00e5ff"  # Cyan
            elif rarity_name == "CURSE":
                rarity_stars = " 💀"
                rarity_color = "#ff1744"  # Red
            elif rarity_name == "STATUS":
                rarity_stars = " 💤"
                rarity_color = "#d500f9"  # Purple

            type_icon = "⚔️"
            if type_str == "SKILL":
                type_icon = "🛡️"
            elif type_str == "POWER":
                type_icon = "🔥"
            elif type_str == "CURSE":
                type_icon = "👻"
            elif type_str == "STATUS":
                type_icon = "💤"
            
            lines.append(f"  [cyan]{i + 1}.[/cyan] {cost_str} {type_icon} [bold {rarity_color}]{card_name}[/]{rarity_stars} [dim]({type_str})[/] ─ [#cdcdcd]{card.description}[/]")
        
        lines.append("")
        # Draw pile with card names
        draw_display = list(reversed(draw_pile))
        if not has_frozen_eye:
            random.shuffle(draw_display)
        draw_names = ", ".join(f"[#d0c0ff]{card.display_name.resolve()}[/]" for card in draw_display) if draw_display else t("ui.empty", default="Empty")
        lines.append(f"[bold #00e676]📥 {t('ui.draw_pile', default='Draw Pile')} ({len(draw_pile)}):[/bold #00e676] {draw_names}")
        
        # Discard pile with card names
        discard_names = ", ".join(f"[#d0c0ff]{card.display_name.resolve()}[/]" for card in discard_pile) if discard_pile else t("ui.empty", default="Empty")
        lines.append(f"[bold #ff9100]📤 {t('ui.discard_pile', default='Discard Pile')} ({len(discard_pile)}):[/bold #ff9100] {discard_names}")
        
        # Exhaust pile (if any)
        exhaust_pile = list(player.card_manager.get_pile("exhaust_pile"))
        if exhaust_pile:
            exhaust_names = ", ".join(f"[#a0a0a0]{card.display_name.resolve()}[/]" for card in exhaust_pile)
            lines.append(f"[bold #ff1744]🔥 {t('ui.exhaust_pile', default='Exhaust')} ({len(exhaust_pile)}):[/bold #ff1744] {exhaust_names}")
        
        if powers:
            lines.append("")
            lines.append(f"[bold #d500f9]✨ {t('combat.powers', default='Powers:')}[/bold #d500f9]")
            for power in powers:
                power_name = power.local("name").resolve() if hasattr(power, 'local') else power.name
                display_amount = power.amount if power.amount is not None else getattr(power, 'duration', None)
                if display_amount is not None and display_amount > 0:
                    lines.append(f"  • [#bd93f9]{power_name}[/] [#d500f9]x{display_amount}[/]")
                else:
                    lines.append(f"  • [#bd93f9]{power_name}[/]")
                    
        # Display relics
        if relics:
            lines.append("")
            lines.append(f"[bold #ffd700]💍 {t('combat.relics', default='Relics:')}[/bold #ffd700]")
            for relic in relics:
                relic_name = relic.local("name").resolve() if hasattr(relic, 'local') else relic.name
                lines.append(f"  • [bold #ffd700]{relic_name}[/]")
        
        # Display potions
        if potions:
            lines.append("")
            lines.append(f"[bold #00e676]🧪 {t('combat.potions', default='Potions:')}[/bold #00e676]")
            for potion in potions:
                if potion is not None:
                    potion_name = potion.local("name").resolve() if hasattr(potion, 'local') else potion.name
                    lines.append(f"  • [#50fa7b]{potion_name}[/]")
        
        # Detailed info section
        lines.append("")
        lines.append(f"[bold #ffd700]📖 {t('combat.details', default='[ DETAILS ]')}[/bold #ffd700]")
        lines.append("─" * 38)
        
        shown_cards = set()
        shown_powers = set()
        shown_relics = set()
        
        all_pile_cards = []
        all_pile_cards.extend(draw_pile)
        all_pile_cards.extend(discard_pile)
        all_pile_cards.extend(exhaust_pile)
        
        card_details = []
        for card in all_pile_cards:
            card_id = card.__class__.__name__
            if card_id not in shown_cards:
                shown_cards.add(card_id)
                card_name = _resolve_text(card, "display_name", card.__class__.__name__)
                card_desc = _resolve_text(card, "combat_description")
                if not card_desc:
                    card_desc = _resolve_text(card, "description")
                if card_desc:
                    card_details.append(f"  [#d0c0ff]{card_name}[/]: {card_desc}")
        
        if card_details:
            lines.append(f"[bold #00e5ff]🎴 {t('combat.card_details', default='Cards:')}[/bold #00e5ff]")
            lines.extend(card_details)
            lines.append("")
            
        power_details = []
        if powers:
            for power in powers:
                power_id = power.__class__.__name__
                if power_id not in shown_powers:
                    shown_powers.add(power_id)
                    power_name = _resolve_text(power, "name", power.__class__.__name__)
                    power_desc = _resolve_text(power, "description")
                    if power_desc and not power_desc.startswith("powers."):
                        power_details.append(f"  [#d500f9]{power_name}[/]: {power_desc}")
                    else:
                        power_details.append(f"  [#d500f9]{power_name}[/]")
                        
        for enemy in combat.enemies:
            if not enemy.is_dead() and hasattr(enemy, 'powers') and enemy.powers:
                for power in enemy.powers:
                    power_id = power.__class__.__name__
                    if power_id not in shown_powers:
                        shown_powers.add(power_id)
                        power_name = _resolve_text(power, "name", power.__class__.__name__)
                        power_desc = _resolve_text(power, "description")
                        if power_desc and not power_desc.startswith("powers."):
                            power_details.append(f"  [#d500f9]{power_name}[/]: {power_desc}")
                        else:
                            power_details.append(f"  [#d500f9]{power_name}[/]")
        if power_details:
            lines.append(f"[bold #d500f9]✨ {t('combat.power_details', default='Powers:')}[/bold #d500f9]")
            lines.extend(power_details)
            lines.append("")
            
        relic_details = []
        if relics:
            for relic in relics:
                relic_id = relic.__class__.__name__
                if relic_id not in shown_relics:
                    shown_relics.add(relic_id)
                    relic_name = _resolve_text(relic, "name", relic.__class__.__name__)
                    relic_desc = _resolve_text(relic, "description")
                    if relic_desc and not relic_desc.startswith("relics."):
                        relic_details.append(f"  [#ffd700]{relic_name}[/]: {relic_desc}")
                    else:
                        relic_details.append(f"  [#ffd700]{relic_name}[/]")
        if relic_details:
            lines.append(f"[bold #ffd700]💍 {t('combat.relic_details', default='Relics:')}[/bold #ffd700]")
            lines.extend(relic_details)   
        
        self._app.update_display_content(lines)
        self.update_player_info(gs)
    
    def display_room(self, room: 'Room', gs: 'GameState'):
        """Display room-specific content."""
        room_type = type(room).__name__
        
        if room_type == "RestRoom":
            self._display_rest_room(room, gs)
        elif room_type == "ShopRoom":
            self._display_shop_room(room, gs)
        elif room_type == "TreasureRoom":
            self._display_treasure_room(room, gs)
        elif room_type == "EventRoom":
            self._display_event_room(room, gs)
        else:
            self._display_generic_room(room, gs)
    
    def _display_rest_room(self, room, gs):
        from localization import t
        bonfire = (
            "          (  )\n"
            "         (    )\n"
            "        (      )\n"
            "       ==========\n"
            "         /\\/\\/\\\n"
        )
        lines = [f"[bold #ff8c00]🔥 {t('rooms.rest.title', default='[ REST ]')}[/bold #ff8c00]"]
        lines.append("─" * 38)
        lines.append("")
        lines.append(f"[bold #ff8c00]{bonfire}[/bold #ff8c00]")
        lines.append(f"[bold white]{t('rooms.rest.description', default='Choose to rest and heal, or upgrade a card.')}[/bold white]")
        self._app.update_display_content("\n".join(lines))
    
    def _display_shop_room(self, room, gs):
        from localization import t
        
        lines = [f"[bold #ffd700]⚖️  {t('rooms.shop.title', default='[ SHOP ]')}[/bold #ffd700]"]
        lines.append("─" * 38)
        lines.append("")
        lines.append(f"[bold #ffd700]🪙 {t('rooms.shop.gold', default=f'Your Gold: {gs.player.gold}')}[/bold #ffd700]")
        lines.append("")
        
        ascension = getattr(gs, 'ascension_level', 0)
        
        # Group items by type
        cards = []
        relics = []
        potions = []
        
        for idx, shop_item in enumerate(room.items):
            if shop_item.purchased:
                continue
            if shop_item.item is None:
                continue
                
            final_price = shop_item.get_final_price_with_modifiers(ascension, gs)
            can_afford = gs.player.gold >= final_price
            
            if shop_item.item_type == "card":
                card_name = shop_item.item.info() if hasattr(shop_item.item, 'info') else str(shop_item.item.name)
                cards.append((idx, card_name, final_price, can_afford))
            elif shop_item.item_type == "relic":
                relic_name = shop_item.item.info() if hasattr(shop_item.item, 'info') else str(shop_item.item.name)
                relics.append((idx, relic_name, final_price, can_afford))
            elif shop_item.item_type == "potion":
                potion_name = shop_item.item.info() if hasattr(shop_item.item, 'info') else str(shop_item.item.name)
                potions.append((idx, potion_name, final_price, can_afford))
        
        # Display cards
        if cards:
            lines.append("[bold #00e5ff]🎴 Cards:[/bold #00e5ff]")
            for idx, name, price, can_afford in cards:
                if can_afford:
                    lines.append(f"  {name} ─ [bold #ffd700]{price}g[/bold #ffd700]")
                else:
                    lines.append(f"  [dim]{name} ─ {price}g (can't afford)[/dim]")
            lines.append("")
        
        # Display relics
        if relics:
            lines.append("[bold #d500f9]💍 Relics:[/bold #d500f9]")
            for idx, name, price, can_afford in relics:
                if can_afford:
                    lines.append(f"  {name} ─ [bold #ffd700]{price}g[/bold #ffd700]")
                else:
                    lines.append(f"  [dim]{name} ─ {price}g (can't afford)[/dim]")
            lines.append("")
        
        # Display potions
        if potions:
            lines.append("[bold #00e676]🧪 Potions:[/bold #00e676]")
            for idx, name, price, can_afford in potions:
                if can_afford:
                    lines.append(f"  {name} ─ [bold #ffd700]{price}g[/bold #ffd700]")
                else:
                    lines.append(f"  [dim]{name} ─ {price}g (can't afford)[/dim]")
            lines.append("")
        
        # Card removal service
        if not room.card_removal_used:
            from rooms.shop import _has_relic
            price = room.card_removal_price
            if _has_relic("SmilingMask", gs):
                price = 50
            elif _has_relic("MembershipCard", gs):
                price = int(price * 0.5)
            can_afford = gs.player.gold >= price
            lines.append("[bold #ff9100]✨ Card Removal:[/bold #ff9100]")
            if can_afford:
                lines.append(f"  Remove a card ─ [bold #ffd700]{price}g[/bold #ffd700]")
            else:
                lines.append(f"  [dim]Remove a card ─ {price}g (can't afford)[/dim]")
        
        self._app.update_display_content("\n".join(lines))
    
    def _display_treasure_room(self, room, gs):
        from localization import t
        chest_art = (
            "        ._________.\n"
            "       /_________/|\n"
            "      |   _ _   ||\n"
            "      |  |_|_|  ||\n"
            "      |_________|/\n"
        )
        lines = [f"[bold #ffd700]💎 {t('rooms.treasure.title', default='[ TREASURE ]')}[/bold #ffd700]"]
        lines.append("─" * 38)
        lines.append("")
        lines.append(f"[bold #ffd700]{chest_art}[/bold #ffd700]")
        lines.append(f"[bold white]{t('rooms.treasure.description', default='A chest awaits!')}[/bold white]")
        self._app.update_display_content("\n".join(lines))
    
    def _display_event_room(self, room, gs):
        from localization import t
        theater_mask = (
            "        🎭  🎭  🎭\n"
            "       未知命运正在等待...\n"
        )
        lines = [f"[bold #d500f9]🎭 {t('rooms.event.title', default='[ EVENT ]')}[/bold #d500f9]"]
        lines.append("─" * 38)
        lines.append("")
        lines.append(f"[bold #d500f9]{theater_mask}[/bold #d500f9]")
        if hasattr(room, 'event') and room.event:
            lines.append(f"[bold white]{str(room.event.name)}[/bold white]")
        self._app.update_display_content("\n".join(lines))
    
    def _display_generic_room(self, room, gs):
        from localization import t
        lines = [f"[bold #a0a0a0]🏛️  {t('rooms.title', default=f'[ {type(room).__name__} ]')}[/bold #a0a0a0]"]
        lines.append("─" * 38)
        self._app.update_display_content("\n".join(lines))
    
    def clear(self):
        """Clear display panel."""
        self._app.update_display_content("")
