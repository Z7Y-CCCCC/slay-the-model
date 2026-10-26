# -*- coding: utf-8 -*-
"""
Entry point for Slay the Model game.
Supports both TUI mode (default) and CLI mode (--no-tui flag).
"""
import sys
import os

# Fix Windows console encoding BEFORE any imports that might print
# if sys.platform == 'win32':
#     import io
#     sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
#     sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import argparse
from engine.game_flow import GameFlow
from engine.game_state import game_state


def _import_character_cards(character: str):
    """Import cards for selected character to register them."""
    if character == "Ironclad":
        import cards.ironclad
    # Add other characters here as they are implemented


def _import_potions():
    """Import potions to register them in the registry."""
    import potions


def _import_powers():
    """Import powers to register them in the registry."""
    from powers import definitions


def _import_relics():
    """Import relics to register them in the registry."""
    import relics


def run_cli_mode():
    """Run game in traditional CLI mode (no TUI)."""
    try:
        # Check if we need to initialize decision engine (in case mode was changed after game_state import)
        if game_state.config.mode == "ai" and game_state.decision_engine is None:
            if game_state.config.ai.get("api_key"):
                from ai.ai_interface import LLMDecisionEngine
                game_state.decision_engine = LLMDecisionEngine(game_state.config.ai, debug=True)
            else:
                print("Warning: AI mode selected but no API key found in config.")

        _import_character_cards(game_state.config.character)
        _import_potions()
        _import_powers()
        _import_relics()
        game = GameFlow()
        game.start_game(game_state)
    except KeyboardInterrupt:
        from localization import t
        print(f"\n{t('ui.game_interrupted', default='Game interrupted by user.')}")
    except Exception as e:
        from localization import t
        print(f"\n{t('ui.game_error', default=f'Game error: {e}', error=e)}")
        import traceback
        traceback.print_exc()


def run_tui_mode():
    """Run game in TUI mode with three-panel layout."""
    try:
        # Check if we need to initialize decision engine
        if game_state.config.mode == "ai" and game_state.decision_engine is None:
            if game_state.config.ai.get("api_key"):
                from ai.ai_interface import LLMDecisionEngine
                game_state.decision_engine = LLMDecisionEngine(game_state.config.ai, debug=True)
        
        # Import all game components first
        _import_character_cards(game_state.config.character)
        _import_potions()
        _import_powers()
        _import_relics()
        
        # Import TUI app
        from tui.app import SlayTheModelApp
        
        # Create and run TUI app
        app = SlayTheModelApp()
        
        # Set AI mode based on config (mode is 'ai' or 'debug' for non-human modes)
        mode = game_state.config.mode
        is_ai_mode = mode in ('ai', 'debug')
        app.set_ai_mode(is_ai_mode)
        
        app.run()
        
    except ImportError as e:
        print(f"TUI not available: {e}")
        print("Falling back to CLI mode...")
        print("Try installing textual: pip install textual")
        run_cli_mode()
    except KeyboardInterrupt:
        from localization import t
        print(f"\n{t('ui.game_interrupted', default='Game interrupted by user.')}")
    except Exception as e:
        from localization import t
        print(f"\n{t('ui.game_error', default=f'Game error: {e}', error=e)}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Slay the Model - A roguelike deck-builder game"
    )
    parser.add_argument(
        "--no-tui",
        action="store_true",
        help="Run in traditional CLI mode without TUI panels"
    )
    parser.add_argument(
        "--tui",
        action="store_true",
        help="Force TUI mode (default)"
    )
    parser.add_argument(
        "--mode",
        choices=["human", "ai", "debug"],
        help="Game mode: human (manual play), ai (LLM control), or debug (random selection)"
    )
    parser.add_argument(
        "--daily",
        action="store_true",
        help="Use today's deterministic daily challenge seed.",
    )
    parser.add_argument(
        "--leaderboard",
        action="store_true",
        help="Print today's daily leaderboard and exit.",
    )
    parser.add_argument(
        "--replay",
        type=str,
        help="Load run setup from replay code.",
    )
    parser.add_argument(
        "--coach",
        action="store_true",
        help="Enable lightweight in-combat coach tips in human mode.",
    )
    parser.add_argument(
        "--no-coach",
        action="store_true",
        help="Disable in-combat coach tips in human mode.",
    )
    
    args = parser.parse_args()

    if args.leaderboard:
        from engine.daily_challenge import format_daily_leaderboard

        print(format_daily_leaderboard())
        return

    if args.replay:
        from engine.replay import apply_replay_settings, decode_replay_code

        try:
            replay_settings = decode_replay_code(args.replay.strip())
            apply_replay_settings(game_state, replay_settings)
            print(f"Loaded replay settings: {replay_settings}")
        except Exception as exc:
            print(f"Invalid replay code: {exc}")
            return

    if args.daily:
        from engine.daily_challenge import get_daily_label, get_daily_seed

        daily_seed = get_daily_seed()
        daily_label = get_daily_label()
        game_state.config.seed = daily_seed
        game_state.daily_mode = True
        game_state.daily_seed_label = daily_label
        print(f"Daily Challenge {daily_label} | Seed: {daily_seed}")
    
    # If mode not provided via CLI, ask interactively
    if args.mode:
        game_state.config.mode = args.mode
    else:
        print("\n=== Choice Game Mode / 选择游戏模式 ===")
        print("1. Human (Manual Play / 人类玩家)")
        print("2. AI (LLM control / AI 自动对战)")
        print("3. Debug (Random Selection / 随机测试)")
        try:
            choice = input("\nEnter choice (1-3) [Default: 1]: ").strip()
            if choice == "2":
                game_state.config.mode = "ai"
            elif choice == "3":
                game_state.config.mode = "debug"
            else:
                game_state.config.mode = "human"
        except EOFError:
            game_state.config.mode = "human"

    if args.coach:
        game_state.config.human["ai_coach"] = True
    elif args.no_coach:
        game_state.config.human["ai_coach"] = False
            
    print(f"Selected Mode: {game_state.config.mode}")

    from engine.replay import build_replay_settings_from_state, encode_replay_code

    game_state.current_replay_code = encode_replay_code(
        build_replay_settings_from_state(game_state)
    )
    print(f"Replay Code: {game_state.current_replay_code}")
    
    if args.no_tui:
        run_cli_mode()
    else:
        run_tui_mode()


if __name__ == "__main__":
    main()
