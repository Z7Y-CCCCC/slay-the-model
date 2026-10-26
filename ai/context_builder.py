# -*- coding: utf-8 -*-
"""
AI Context Builder - Builds comprehensive game state context for LLM decision making.

This module constructs a detailed, human-readable context string that includes:
- Player status (HP, energy, gold, floor, block)
- Relics with full descriptions
- Powers on player with full descriptions
- Combat status (enemies, hand cards, deck piles)
- All card/relic/power descriptions are included (AI has no prior knowledge)
"""
from typing import TYPE_CHECKING

from localization import t

if TYPE_CHECKING:
    from engine.game_state import GameState
    from engine.combat import Combat


class AIContextBuilder:
    """Builds comprehensive game state context for AI decision making.
    
    The output is formatted as Markdown for optimal LLM readability.
    Reuses the structure from DisplayHandler but enhances with full descriptions.
    """
    
    @staticmethod
    def build_context(gs: 'GameState') -> str:
        """Build complete context string for AI decision making.
        
        Args:
            gs: GameState instance
            
        Returns:
            Markdown-formatted string containing game state information
        """
        sections = []
        
        # 1. Player base status
        sections.append(AIContextBuilder._build_player_status(gs))
        
        # 2. Relics with full descriptions
        if gs.player.relics:
            sections.append(AIContextBuilder._build_relics_info(gs))
        
        # 3. Powers on player with full descriptions
        if gs.player.powers:
            sections.append(AIContextBuilder._build_player_powers(gs))
        
        # 4. Combat status (if in combat)
        if gs.current_combat:
            sections.append(AIContextBuilder._build_combat_status(gs))
        
        # 5. Non-combat room info (if applicable)
        elif gs.current_room:
            sections.append(AIContextBuilder._build_room_info(gs))
        
        return "\n\n".join(filter(None, sections))
    
    @staticmethod
    def _build_player_status(gs: 'GameState') -> str:
        """Shorter player status for AI."""
        player = gs.player
        # Extreme shorthand to save bytes
        return f"# [STAT] {player.hp}/{player.max_hp}HP|{player.energy}/{player.max_energy}E|{player.gold}G|F:{gs.current_floor + 1}|B:{player.block}"
    
    @staticmethod
    def _build_relics_info(gs: 'GameState') -> str:
        """Build relics section with full descriptions."""
        player = gs.player
        lines = [f"## {t('ai_context.relics')} ({len(player.relics)})"]
        
        for i, relic in enumerate(player.relics, 1):
            name = relic.local("name").resolve()
            if i <= 8: # Only show descriptions for first 8 relics
                desc = relic.local("description").resolve()
                desc = desc.replace("{amount}", str(getattr(relic, 'amount', '')))
                lines.append(f"{i}. **{name}**: {desc}")
            else:
                lines.append(f"{i}. **{name}**")
        
        if len(player.relics) > 8:
            lines.append(f"*(Remaining {len(player.relics) - 8} relics omitted)*")
        
        return "\n".join(lines)
    
    @staticmethod
    def _build_player_powers(gs: 'GameState') -> str:
        """Build player powers with intelligent filtering."""
        player = gs.player
        lines = [f"## [POWERS]"]
        
        # Known common powers skip description for speed/tokens
        COMMON_POWERS = ["力量", "敏捷", "格挡", "易伤", "虚弱", "脆弱", "人工制品", "中毒", "荆棘", "金属化", "壁垒", "多重打击"]
        
        for i, power in enumerate(player.powers, 1):
            name = power.local("name").resolve()
            amt_str = f"x{power.amount}" if power.amount > 0 else ""
            
            # Skip description if common or many powers
            if name in COMMON_POWERS or i > 3:
                lines.append(f"{i}. {name}{amt_str}")
            else:
                desc = power.local("description").resolve().replace("{amount}", str(power.amount))
                lines.append(f"{i}. {name}{amt_str}: {desc}")
        
        return "\n".join(lines)
    
    @staticmethod
    def _build_combat_status(gs: 'GameState') -> str:
        """Build combat status section with full information."""
        combat = gs.current_combat
        player = gs.player
        
        # Get card piles
        hand = list(player.card_manager.get_pile("hand"))
        draw_pile = list(player.card_manager.get_pile("draw_pile"))
        discard = list(player.card_manager.get_pile("discard_pile"))
        exhaust = list(player.card_manager.get_pile("exhaust_pile"))
        
        sections = [f"# {t('ai_context.combat_status')}"]
        
        # Enemies with full info
        alive_enemies = [e for e in combat.enemies if not e.is_dead()]
        
        # Build enemy section
        enemy_lines = [f"## {t('ai_context.enemies')}"]
        if not alive_enemies:
            enemy_lines.append(t('ai_context.no_enemies'))
        else:
            for i, enemy in enumerate(alive_enemies, 1):
                # Enemy name
                if hasattr(enemy, 'local'):
                    name = enemy.local("name").resolve()
                else:
                    name = getattr(enemy, 'name', str(enemy.__class__.__name__))
                
                enemy_lines.append(f"{i}. **{name}** {enemy.hp}/{enemy.max_hp}HP|B:{enemy.block}")
                
                # Intent
                if hasattr(enemy, 'current_intention') and enemy.current_intention:
                    intent_str = AIContextBuilder._format_intent(enemy.current_intention)
                    enemy_lines.append(f"   - [INT]: {intent_str}")
                
                # Enemy powers (filtered)
                COMMON = ["力量", "敏捷", "格挡", "易伤", "虚弱", "脆弱", "人工制品", "中毒", "荆棘", "仪式", "愤怒"]
                if enemy.powers:
                    for power in enemy.powers:
                        pname = power.local("name").resolve()
                        pamt = f"x{power.amount}" if power.amount > 0 else ""
                        if pname in COMMON:
                            enemy_lines.append(f"   - [P]: {pname}{pamt}")
                        else:
                            pdesc = power.local("description").resolve().replace("{amount}", str(power.amount))
                            enemy_lines.append(f"   - [P]: {pname}{pamt}: {pdesc}")
        
        sections.append("\n".join(enemy_lines))
        
        # Hand cards with full info
        hand_lines = [f"## {t('ai_context.hand')} ({len(hand)} {t('ai_context.cards')})"]
        # Add note about damage/block calculation
        hand_lines.append(f"*{t('ai_context.card_stats_note')}*")
        
        for i, card in enumerate(hand, 1):
            card_info = AIContextBuilder._format_card_info(card)
            hand_lines.append(f"{i}. {card_info}")
        
        sections.append("\n".join(hand_lines))
        
        # Smart grouping for token saving (Senior Designer Optimization)
        def _truncate_pile(pile, limit=8):
            if not pile:
                return t('ui.empty')
            
            # Count identical cards
            counts = {}
            for c in pile:
                name = AIContextBuilder._get_card_name(c)
                counts[name] = counts.get(name, 0) + 1
            
            # Format as "Name xCount"
            formatted = []
            for name, count in counts.items():
                if count > 1:
                    formatted.append(f"{name}x{count}")
                else:
                    formatted.append(name)
            
            # Limit the number of unique types shown to avoid prompt explosion
            if len(formatted) <= limit:
                return ", ".join(formatted)
            return ", ".join(formatted[:limit]) + f" ... (+{len(formatted) - limit} {t('ai_context.cards_total')})"

        draw_line = f"{t('combat.draw_pile')} ({len(draw_pile)}): {_truncate_pile(draw_pile)}"
        discard_line = f"{t('combat.discard_pile')} ({len(discard)}): {_truncate_pile(discard)}"
        exhaust_line = f"{t('combat.exhaust_pile', default='Exhaust Pile')} ({len(exhaust)}): {_truncate_pile(exhaust)}"
        
        sections.append(f"## {t('ai_context.deck_status')}\n" + "\n".join([draw_line, discard_line, exhaust_line]))
        
        return "\n\n".join(sections)
    
    @staticmethod
    def _build_room_info(gs: 'GameState') -> str:
        """Build non-combat room information."""
        room = gs.current_room
        if not room:
            return ""
        
        room_type = type(room).__name__
        lines = [f"# [ROOM]: {room_type}"]
        
        # Add room-specific info based on type
        if room_type == "ShopRoom":
            lines.append(AIContextBuilder._build_shop_info(room))
        elif room_type == "RestRoom":
            lines.append("[REST]: Heal 30% or Smith Upgrade")
        
        return "\n".join(lines)
    
    @staticmethod
    def _build_shop_info(room) -> str:
        """Build shop item information."""
        lines = [f"## {t('ai_context.shop_items')}"]
        
        # Cards for sale
        if hasattr(room, 'cards') and room.cards:
            lines.append(f"### {t('ai_context.cards_for_sale')}:")
            for i, card in enumerate(room.cards, 1):
                price = getattr(card, 'price', '?')
                card_info = AIContextBuilder._format_card_info(card)
                lines.append(f"{i}. {card_info} - {t('ai_context.price')}: {price}g")
        
        # Relics for sale
        if hasattr(room, 'relics') and room.relics:
            lines.append(f"### {t('ai_context.relics_for_sale')}:")
            for i, relic in enumerate(room.relics, 1):
                price = getattr(relic, 'price', '?')
                name = relic.local("name").resolve()
                desc = relic.local("description").resolve()
                lines.append(f"{i}. **{name}**: {desc} - {t('ai_context.price')}: {price}g")
        
        # Potions for sale
        if hasattr(room, 'potions') and room.potions:
            lines.append(f"### {t('ai_context.potions_for_sale')}:")
            for i, potion in enumerate(room.potions, 1):
                price = getattr(potion, 'price', '?')
                name = potion.local("name").resolve()
                desc = potion.local("description").resolve()
                lines.append(f"{i}. **{name}**: {desc} - {t('ai_context.price')}: {price}g")
        
        # Card removal service
        lines.append(f"### {t('ai_context.services')}:")
        lines.append(f"- {t('ai_context.remove_card_service')}")
        
        return "\n".join(lines)
    
    @staticmethod
    def _format_card_info(card) -> str:
        """Extreme card info for AI."""
        # Name
        if hasattr(card, 'display_name'):
            name = card.display_name.resolve()
        elif hasattr(card, 'local'):
            name = card.local("name").resolve()
        else:
            name = card.__class__.__name__
        
        cost = card.cost if hasattr(card, 'cost') and card.cost is not None else 0
        cost_str = str(cost) if cost >= 0 else "X"
        
        # Stats
        stats = []
        if hasattr(card, 'damage') and card.damage and card.damage > 0:
            stats.append(f"D:{card.damage}")
        if hasattr(card, 'block') and card.block and card.block > 0:
            stats.append(f"B:{card.block}")
        stats_str = f"({','.join(stats)})" if stats else ""
        
        # Skip descriptions for starters/obvious cards
        STARTERS = ["打击", "防御", "打击+", "防御+", "重击", "重击+"]
        desc = ""
        if name not in STARTERS and hasattr(card, 'local'):
            desc = card.local("description").resolve()
            if hasattr(card, 'damage') and card.damage:
                desc = desc.replace("{damage}", str(card.damage))
            if hasattr(card, 'block') and card.block:
                desc = desc.replace("{block}", str(card.block))
            if hasattr(card, '_magic') and card._magic:
                for mk, mv in card._magic.items():
                    desc = desc.replace(f"{{magic.{mk}}}", str(mv))
        
        res = f"**[{cost_str}] {name} {stats_str}**"
        if desc:
            # Inline description for more compactness
            res += f" - {desc}"
        
        return res
    
    @staticmethod
    def _get_card_name(card) -> str:
        """Get just the name of a card."""
        if hasattr(card, 'display_name'):
            return card.display_name.resolve()
        elif hasattr(card, 'local'):
            return card.local("name").resolve()
        else:
            return card.__class__.__name__
    
    @staticmethod
    def _format_intent(intent) -> str:
        """Format enemy intent for readability."""
        if not intent:
            return t('ui.unknown', default='Unknown')
        
        # First try to get the description from the intent object
        if hasattr(intent, 'description'):
            desc = intent.description
            if hasattr(desc, 'resolve'):
                return desc.resolve()
            return str(desc)
        
        # Fallback: try to get intent name
        if hasattr(intent, 'name'):
            return str(intent.name)
        
        # Last resort: return Unknown
        return "Unknown"
