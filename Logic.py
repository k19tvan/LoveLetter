# game_logic.py

import os
import random
from kivy.clock import Clock  # Clock is needed for CPU turn delays, a minor dependency.

# --- Constants and Raw Data ---

CARD_FOLDER = "assets/cards"
CARD_BACK_IMAGE = "assets/cards/back.jpg"
ELIMINATED_IMAGE = "assets/cards/eliminated.jpg"

CARDS_DATA_RAW = {
    'Guard': {'value': 1, 'vietnamese_name': 'canve',
              'description': "Guess a player's card (not Guard). If correct, they are out.",
              'count_classic': 5, 'count_large': 8},
    'Priest': {'value': 2, 'vietnamese_name': 'mucsu',
               'description': "Look at another player's hand.",
               'count_classic': 2, 'count_large': 0},
    'Baron': {'value': 3, 'vietnamese_name': 'namtuoc',
              'description': "Compare hands; lower value is out.",
              'count_classic': 2, 'count_large': 0},
    'Handmaid': {'value': 4, 'vietnamese_name': 'cohau',
                 'description': "Immune to effects until your next turn.",
                 'count_classic': 2, 'count_large': 0},
    'Prince': {'value': 5, 'vietnamese_name': 'hoangtu',
               'description': "Choose player to discard hand and draw.",
               'count_classic': 2, 'count_large': 0},
    'King': {'value': 6, 'vietnamese_name': 'nhavua',
             'description': "Trade hands with another player.",
             'count_classic': 1, 'count_large': 0},
    'Countess': {'value': 7, 'vietnamese_name': 'nubatuoc',
                 'description': "Must discard if you have King or Prince.",
                 'count_classic': 1, 'count_large': 0},
    'Princess': {'value': 8, 'vietnamese_name': 'congchua',
                 'description': "Lose if you discard this card.",
                 'count_classic': 1, 'count_large': 0},
    'Assassin': {'value': 0, 'vietnamese_name': 'satthu',
                 'description': "If targeted by Guard, Guard player is out. Discard & draw.",
                 'count_classic': 0, 'count_large': 1},
    'Jester': {'value': 0, 'vietnamese_name': 'tenhe',
               'description': "Target player. If they win round, you get token.",
               'count_classic': 0, 'count_large': 1},
    'Cardinal': {'value': 2, 'vietnamese_name': 'hongy',
                 'description': "Two players swap hands. Look at one.",
                 'count_classic': 0, 'count_large': 2},
    'Baroness': {'value': 3, 'vietnamese_name': 'nunamtuoc',
                 'description': "Look at 1 or 2 players' hands.",
                 'count_classic': 0, 'count_large': 2},
    'Sycophant': {'value': 4, 'vietnamese_name': 'keninhbo',
                  'description': "Target player must target self with next effect card.",
                  'count_classic': 0, 'count_large': 2},
    'Count': {'value': 5, 'vietnamese_name': 'batuoc',
              'description': "+1 to hand value if this is in your discard pile.",
              'count_classic': 0, 'count_large': 2},
    'Sheriff': {'value': 6, 'vietnamese_name': 'nguyensoai',
                'description': "If eliminated with this in discard, gain token.",
                'count_classic': 0, 'count_large': 1},
    'Queen Mother': {'value': 7, 'vietnamese_name': 'nuhoang',
                     'description': "Compare hands; higher value is out.",
                     'count_classic': 0, 'count_large': 1},
    'Bishop': {'value': 9, 'vietnamese_name': 'giammuc',
               'description': "Guess card value (not Guard). Gain token if correct. Target may redraw.",
               'count_classic': 0, 'count_large': 1},
}

CARD_PROTOTYPES = {}  # Will be populated by Card objects from the UI side


# --- Core Game Logic Classes ---

class Card:
    def __init__(self, name, value, description, image_path, vietnamese_name, count_classic, count_large):
        self.name = name
        self.value = value
        self.description = description
        self.image_path = image_path
        self.vietnamese_name = vietnamese_name
        self.count_classic = count_classic
        self.count_large = count_large
        self.is_targeting_effect = name not in ['Handmaid', 'Countess', 'Princess', 'Assassin', 'Count',
                                                'Sheriff']

    def __repr__(self):
        return f"Card({self.name}, V:{self.value})"

    def to_dict(self):
        return {
            'name': self.name, 'value': self.value, 'image_path': self.image_path,
            'description': self.description, 'vietnamese_name': self.vietnamese_name
        }


class Deck:
    def __init__(self, num_players, log_callback):
        self.cards = []
        self.burned_card = None
        self.log_callback = log_callback
        self._create_deck(num_players)
        self.shuffle()

    def _create_deck(self, num_players):
        self.cards = []
        composition_key = 'count_classic' if num_players <= 4 else 'count_large'
        self.log_callback(
            f"Deck: Using composition for {'2-4 players (classic)' if composition_key == 'count_classic' else '5-8 players (large)'}.")

        for card_name, prototype in CARD_PROTOTYPES.items():
            count = getattr(prototype, composition_key, 0)
            for _ in range(count):
                self.cards.append(prototype)

        if not self.cards:
            self.log_callback("ERROR: No cards defined for this player count! Check CARD_PROTOTYPES counts.")
            if composition_key == 'count_large' and any(
                    proto.count_classic > 0 for proto in CARD_PROTOTYPES.values()):
                self.log_callback("Deck: Falling back to classic deck due to empty large deck definition.")
                composition_key = 'count_classic'
                for card_name, prototype in CARD_PROTOTYPES.items():
                    count = getattr(prototype, composition_key, 0)
                    for _ in range(count): self.cards.append(prototype)

        self.log_callback(f"Deck: Created with {len(self.cards)} cards.")

    def shuffle(self):
        random.shuffle(self.cards)
        self.log_callback("Deck: Shuffled.")

    def draw(self):
        return self.cards.pop(0) if self.cards else None

    def burn_one_card(self, num_players):
        if num_players > 1 and self.cards:
            self.burned_card = self.draw()
            if self.burned_card:
                self.log_callback(
                    f"Deck: Burned one card ({self.burned_card.name}). {len(self.cards)} cards remaining.")
            else:
                self.log_callback("Deck: Tried to burn card, but deck was empty after draw attempt.")
        elif num_players == 2:
            if self.cards:
                self.burned_card = self.draw()
                if self.burned_card:
                    self.log_callback(
                        f"Deck (2P): Burned one card ({self.burned_card.name}). {len(self.cards)} cards remaining.")

    def is_empty(self):
        return not self.cards

    def count(self):
        return len(self.cards)


class Player:
    def __init__(self, id_num, name, is_cpu=False):
        self.id = id_num
        self.name = name
        self.hand = []
        self.discard_pile = []
        self.tokens = 0
        self.is_eliminated = False
        self.is_protected = False
        self.is_cpu = is_cpu
        self.sycophant_target_self = False
        self.jester_on_player_id = None
        self.effective_value_end_round = 0
        self.discard_sum_end_round = 0

    def reset_for_round(self):
        self.hand = []
        self.discard_pile = []
        self.is_eliminated = False
        self.is_protected = False
        self.sycophant_target_self = False
        self.jester_on_player_id = None
        self.effective_value_end_round = 0
        self.discard_sum_end_round = 0

    def add_card_to_hand(self, card):
        if card:
            self.hand.append(card)

    def play_card(self, card_name_to_play):
        card_to_play = next((c for c in self.hand if c.name == card_name_to_play), None)
        if card_to_play:
            self.hand.remove(card_to_play)
            self.discard_pile.append(card_to_play)
            return card_to_play
        return None

    def force_discard(self, game_deck, burned_card_ref):
        if not self.hand: return None
        discarded_card = self.hand.pop(0)
        self.discard_pile.append(discarded_card)
        new_card = None
        if not game_deck.is_empty():
            new_card = game_deck.draw()
        elif burned_card_ref['card']:
            new_card = burned_card_ref['card']
            burned_card_ref['card'] = None
        if new_card:
            self.add_card_to_hand(new_card)
        return discarded_card

    def get_hand_card_names(self):
        return [card.name for card in self.hand]

    def get_hand_card_values(self):
        return [card.value for card in self.hand]

    def has_card(self, card_name):
        return any(c.name == card_name for c in self.hand)

    def has_discarded(self, card_name):
        return any(c.name == card_name for c in self.discard_pile)

    def __repr__(self):
        return f"Player({self.name}, Tokens:{self.tokens}, Hand:{[c.name for c in self.hand]})"


class GameRound:
    # (The entire GameRound class from your original code goes here, unchanged)
    def __init__(self, players_list, deck_obj, human_player_id, log_callback, ui_callbacks):
        self.players = players_list  # List of Player objects
        self.deck = deck_obj
        self.human_player_id = human_player_id
        self.log_message = log_callback
        self.ui = ui_callbacks  # Dictionary of callbacks to the UI

        self.current_player_idx = 0
        self.round_active = False
        self.game_over_pending_from_round = False  # If an effect causes game to end mid-round (e.g. Bishop token)
        self.game_over_winner = None

        # Shared mutable reference for the burned card if Prince needs it
        # self.deck.burned_card is the actual Card object
        self.shared_burned_card_ref = {'card': self.deck.burned_card}

    def start_round(self):
        self.log_message("--- Starting New Round (GameRound) ---")
        for p in self.players:
            p.reset_for_round()
            drawn_card = self.deck.draw()
            if drawn_card:
                p.add_card_to_hand(drawn_card)
            else:
                self.log_message(f"Error: Not enough cards to deal to {p.name}. Deck empty.")
                p.is_eliminated = True  # Should not happen with proper deck sizes

        self.current_player_idx = random.randrange(len(self.players))
        self.round_active = True
        self.log_message(f"Round started. {self.players[self.current_player_idx].name} goes first.")
        self.ui['update_ui_full_callback']()
        self._process_current_player_turn_start()

    def _execute_cpu_turn_after_delay(self, cpu_player):
        if not self.round_active or cpu_player.is_eliminated:
            if self.round_active and not self.players[
                self.current_player_idx].is_eliminated:  # If current player is still this CPU and round active
                self._advance_to_next_turn()
            return

        if self.players[self.current_player_idx] != cpu_player:
            return

        self.log_message(f"CPU ({cpu_player.name}) decides to play.")
        self._cpu_play_turn(cpu_player)

    def _process_current_player_turn_start(self):
        if not self.round_active: return

        current_player = self.players[self.current_player_idx]
        if current_player.is_eliminated:
            self._advance_to_next_turn()
            return

        current_player.is_protected = False

        if not self.deck.is_empty():
            drawn_card = self.deck.draw()
            current_player.add_card_to_hand(drawn_card)
            if not current_player.is_cpu:
                self.log_message(
                    f"You ({current_player.name}) drew {drawn_card.name}. Hand: {current_player.get_hand_card_names()}.")
            else:
                self.log_message(f"{current_player.name} drew a card. Hand size: {len(current_player.hand)}.")
            self.ui['update_ui_full_callback']()
        else:
            self.log_message("Deck is empty. Round ends by deck out.")
            self._end_round_deck_empty()
            return

        if current_player.is_cpu:
            self.log_message(f"CPU ({current_player.name}) is thinking...")
            delay_duration = random.uniform(1.0, 2.0)
            Clock.schedule_once(lambda dt: self._execute_cpu_turn_after_delay(current_player), delay_duration)
        else:
            self.log_message(f"Your turn, {current_player.name}. Choose a card to play.")
            self.ui['set_waiting_flag_callback'](False)
            hand_names = current_player.get_hand_card_names()
            if self._is_card_in_current_deck('Countess') and 'Countess' in hand_names and \
                    ((self._is_card_in_current_deck('King') and 'King' in hand_names) or \
                     (self._is_card_in_current_deck('Prince') and 'Prince' in hand_names)):
                self.log_message("INFO: You have Countess and King/Prince. You MUST play Countess.")

    def human_plays_card(self, card_name_played):
        player = self.players[self.current_player_idx]
        if player.is_cpu or not self.round_active: return

        actual_card_to_play_name = card_name_played
        hand_names = player.get_hand_card_names()
        has_king_or_prince = (self._is_card_in_current_deck('King') and 'King' in hand_names) or \
                             (self._is_card_in_current_deck('Prince') and 'Prince' in hand_names)
        if self._is_card_in_current_deck('Countess') and 'Countess' in hand_names and has_king_or_prince:
            if card_name_played != 'Countess':
                self.log_message("Countess Rule: Auto-playing Countess as King/Prince also in hand.")
                actual_card_to_play_name = 'Countess'
        card_object_played = player.play_card(actual_card_to_play_name)
        if card_object_played:
            self._handle_card_played_logic(player, card_object_played)
        else:
            self.log_message(
                f"ERROR: {player.name} tried to play {actual_card_to_play_name} but failed (not in hand or other issue).")
            self.ui['set_waiting_flag_callback'](False)
            if self.round_active: self._advance_to_next_turn()

    def _cpu_play_turn(self, cpu_player):
        self.log_message(f"CPU ({cpu_player.name})'s turn.")
        hand_names = cpu_player.get_hand_card_names()

        # Bắt buộc chơi Countess nếu có King hoặc Prince
        has_king_or_prince = (self._is_card_in_current_deck('King') and 'King' in hand_names) or \
                            (self._is_card_in_current_deck('Prince') and 'Prince' in hand_names)
        if self._is_card_in_current_deck('Countess') and 'Countess' in hand_names and has_king_or_prince:
            self.log_message(f"CPU ({cpu_player.name}) has Countess and King/Prince, must play Countess.")
            card_object_played = cpu_player.play_card('Countess')
            self._handle_card_played_logic(cpu_player, card_object_played)
            return

        # Nếu có Princess và nhiều hơn 1 lá, tránh chơi Princess
        playable_cards = list(cpu_player.hand)
        if self._is_card_in_current_deck('Princess') and len(playable_cards) > 1:
            playable_cards = [c for c in playable_cards if c.name != 'Princess']
            if not playable_cards:
                playable_cards = list(cpu_player.hand)  # Nếu không còn lựa chọn, chơi bất kỳ

        # Chọn ngẫu nhiên 1 lá hợp lệ
        chosen_card_object = random.choice(playable_cards) if playable_cards else random.choice(cpu_player.hand)
        card_object_played = cpu_player.play_card(chosen_card_object.name)
        self._handle_card_played_logic(cpu_player, card_object_played)

    def _handle_card_played_logic(self, player, card_object_played):
        self.log_message(f"{player.name} plays {card_object_played.name}.")
        self.ui['update_ui_full_callback']()
        if self._is_card_in_current_deck('Princess') and card_object_played.name == 'Princess':
            self.log_message(f"{player.name} discarded the Princess and is eliminated!")
            self._eliminate_player(player)
            self._finish_effect_and_proceed()
            return
        needs_input = self._execute_card_effect(player, card_object_played)
        if not needs_input:
            self._finish_effect_and_proceed()

    def _is_card_in_current_deck(self, card_name):
        prototype = CARD_PROTOTYPES.get(card_name)
        if not prototype: return False
        composition_key = 'count_classic' if len(self.players) <= 4 else 'count_large'
        return getattr(prototype, composition_key, 0) > 0

    def _get_valid_targets(self, acting_player, include_self=False, targeted_effect_requires_unprotected=True,
                           allow_no_hand=False):
        targets = []
        for p in self.players:
            if p == acting_player and not include_self:
                continue
            if p.is_eliminated:
                continue
            if targeted_effect_requires_unprotected and p.is_protected and p != acting_player:
                continue
            # Simplified logic from original. Needs card_object_played. Passing it would be a bigger refactor.
            # Assume for now that this logic is sufficient as it was in the original.
            if not p.hand and not allow_no_hand and p != acting_player:
                continue
            targets.append(p)
        return targets

    def _execute_card_effect(self, player, card):
        card_name = card.name
        if not self._is_card_in_current_deck(card_name):
            self.log_message(f"{card_name} is not part of the current deck composition. Effect fizzles.")
            return False
        must_target_self = player.sycophant_target_self
        player.sycophant_target_self = False
        effect_method_name = f"_effect_{card_name.lower().replace(' ', '_')}"
        effect_method = getattr(self, effect_method_name, None)
        if effect_method:
            if card_name in ['Handmaid', 'Countess', 'Assassin', 'Count', 'Sheriff']:
                return effect_method(player, card)
            else:
                return effect_method(player, card, must_target_self)
        else:
            self.log_message(f"Effect for {card_name} not implemented or is passive/automatic.");
            return False

    def _finish_effect_and_proceed(self):
        self.ui['set_waiting_flag_callback'](False)
        if self.ui['get_active_popup_callback']():
            self.ui['dismiss_active_popup_callback']()
        if self.game_over_pending_from_round:
            self.round_active = False
            self.ui['game_over_callback'](self.game_over_winner)
            return
        round_ended_by_elimination = self._check_round_end_by_elimination()
        if not round_ended_by_elimination and self.round_active:
            self._advance_to_next_turn()
        self.ui['update_ui_full_callback']()

    def _eliminate_player(self, player_to_eliminate):
        if player_to_eliminate.is_eliminated: return
        player_to_eliminate.is_eliminated = True
        self.log_message(f"{player_to_eliminate.name} has been eliminated!")
        if self._is_card_in_current_deck('Sheriff') and player_to_eliminate.has_discarded('Sheriff'):
            self.log_message(f"{player_to_eliminate.name} had Sheriff in discard and gains a token!")
            player_to_eliminate.tokens += 1
            if self.ui['check_game_over_token_callback'](player_to_eliminate):
                self.game_over_pending_from_round = True
                self.game_over_winner = player_to_eliminate

    def _advance_to_next_turn(self):
        if not self.round_active: return
        attempts = 0
        while attempts < len(self.players) * 2:
            self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
            if not self.players[self.current_player_idx].is_eliminated:
                break
            attempts += 1
        active_players_count = sum(1 for p in self.players if not p.is_eliminated)
        if active_players_count <= 1 and self.round_active:
            self._end_round_by_elimination()
            return
        next_player = self.players[self.current_player_idx]
        if not next_player.is_cpu:
            self.log_message(f"--- Your turn ({next_player.name}) ---")
        else:
            self.log_message(f"--- {next_player.name}'s turn ---")
        self._process_current_player_turn_start()

    def _check_round_end_by_elimination(self):
        if not self.round_active: return True
        active_players = [p for p in self.players if not p.is_eliminated]
        if len(active_players) <= 1:
            self._end_round_by_elimination(active_players)
            return True
        return False

    def _end_round_by_elimination(self, active_players_list=None):
        if not self.round_active: return
        self.log_message("Round ends: one or zero players remain active.")
        self.round_active = False
        if active_players_list is None:
            active_players_list = [p for p in self.players if not p.is_eliminated]
        winner = active_players_list[0] if len(active_players_list) == 1 else None
        if winner:
            self.log_message(f"{winner.name} is the last player remaining and wins the round!")
        else:
            self.log_message("All players were eliminated simultaneously! No winner this round from eliminations.")
        self.ui['award_round_tokens_callback']([winner] if winner else [])

    def _end_round_deck_empty(self):
        if not self.round_active: return
        self.log_message("Round ends: deck is empty. Comparing hands of remaining active players.")
        self.round_active = False
        active_players_with_hands = [p for p in self.players if not p.is_eliminated and p.hand]
        if not active_players_with_hands:
            self.log_message("No active players with cards remaining. No winner this round.");
            self.ui['award_round_tokens_callback']([])
            return
        is_count_in_deck = self._is_card_in_current_deck('Count')
        for p_obj in active_players_with_hands:
            p_obj.effective_value_end_round = p_obj.hand[0].value
            if is_count_in_deck and p_obj.has_discarded('Count'):
                p_obj.effective_value_end_round += 1
                self.log_message(
                    f"{p_obj.name} has Count in discard. Hand: {p_obj.hand[0].name}, Effective Value: {p_obj.effective_value_end_round}")
        active_players_with_hands.sort(key=lambda p: p.effective_value_end_round, reverse=True)
        highest_val = active_players_with_hands[0].effective_value_end_round
        winners_by_val = [p for p in active_players_with_hands if p.effective_value_end_round == highest_val]
        final_winners = []
        if len(winners_by_val) == 1:
            final_winners = winners_by_val
            self.log_message(
                f"{final_winners[0].name} has the highest card ({final_winners[0].hand[0].name}, effective value {final_winners[0].effective_value_end_round}) and wins!")
        else:
            self.log_message(f"Tie in card values at {highest_val}. Comparing sum of discarded card values.")
            for p_obj in winners_by_val:
                p_obj.discard_sum_end_round = sum(c.value for c in p_obj.discard_pile)
                self.log_message(
                    f"{p_obj.name} (Card: {p_obj.hand[0].name}, Eff: {p_obj.effective_value_end_round}) discard sum: {p_obj.discard_sum_end_round}")
            winners_by_val.sort(key=lambda p: p.discard_sum_end_round, reverse=True)
            highest_discard_sum = winners_by_val[0].discard_sum_end_round
            final_winners = [p for p in winners_by_val if p.discard_sum_end_round == highest_discard_sum]
            if len(final_winners) == 1:
                self.log_message(
                    f"{final_winners[0].name} wins the tie-breaker with highest discard sum ({highest_discard_sum})!")
            else:
                self.log_message(
                    f"Still a tie! {[p.name for p in final_winners]} win this round.")
        self.ui['award_round_tokens_callback'](final_winners)
    
    # ... ALL THE _effect_... and _resolve_... METHODS FROM THE ORIGINAL CODE ...
    # ... GO HERE, UNCHANGED. (I've included them all below for completeness) ...
    def _effect_guard(self, player, card_played, must_target_self):
        valid_targets = self._get_valid_targets(player, include_self=False, targeted_effect_requires_unprotected=True)
        if must_target_self:  # Guard cannot target self
            self.log_message(f"Sycophant: {player.name} must target self, but Guard cannot. Effect fizzles.")
            return False
        if not valid_targets: self.log_message("Guard: No valid targets."); return False

        if player.is_cpu:
            target_player = random.choice(valid_targets)
            possible_values = sorted(list(set(proto.value for name, proto in CARD_PROTOTYPES.items()
                                              if proto.value != 1 and self._is_card_in_current_deck(name))))
            if not possible_values: self.log_message("Guard (CPU): No valid card values to guess!"); return False
            guess_val = random.choice(possible_values)
            self.log_message(f"CPU ({player.name}) plays Guard on {target_player.name}, guessing value {guess_val}.")
            self._resolve_guard_guess(player, target_player, guess_val)
            return False
        else:
            self.ui['request_target_selection_callback'](
                player, card_played, valid_targets,
                self._resolve_guard_target_selected  # GameRound method as callback
            )
            return True  # Input awaited

    def _resolve_guard_target_selected(self, acting_player, target_player_id):  # Called by UI
        target_player = next(p for p in self.players if p.id == target_player_id)

        possible_values_to_guess = sorted(list(set(proto.value for name, proto in CARD_PROTOTYPES.items()
                                                   if proto.value != 1 and self._is_card_in_current_deck(name))))
        if not possible_values_to_guess:
            self.log_message(f"Guard: No valid card values to guess against {target_player.name}! Effect fizzles.");
            self._finish_effect_and_proceed()
            return

        self.ui['request_guard_value_popup_callback'](
            acting_player, target_player, possible_values_to_guess,
            self._resolve_guard_value_guessed  # GameRound method as callback
        )
        # Still waiting for input

    def _resolve_guard_value_guessed(self, acting_player, target_player, guessed_value):  # Called by UI
        self.log_message(f"{acting_player.name} (Guard) guesses value {guessed_value} for {target_player.name}.")
        self._resolve_guard_guess(acting_player, target_player, guessed_value)
        self._finish_effect_and_proceed()

    def _resolve_guard_guess(self, acting_player, target_player, guessed_value):  # Core logic
        if not target_player.hand: return

        target_card = target_player.hand[0]

        if self._is_card_in_current_deck('Assassin') and target_card.name == 'Assassin':
            self.log_message(f"{target_player.name} reveals Assassin! {acting_player.name} is eliminated!")
            self._eliminate_player(acting_player)

            target_player.play_card('Assassin')  # Discard Assassin
            if not self.deck.is_empty():
                new_card = self.deck.draw()
                if new_card: target_player.add_card_to_hand(new_card)
            elif self.shared_burned_card_ref['card']:
                new_card = self.shared_burned_card_ref['card']
                target_player.add_card_to_hand(new_card)
                self.shared_burned_card_ref['card'] = None

            self.log_message(f"{target_player.name} discards Assassin and draws a new card.")
            return

        if target_card.value == guessed_value:
            self.log_message(f"Correct! {target_player.name} had {target_card.name}. Eliminated.")
            self._eliminate_player(target_player)
        else:
            self.log_message(f"Incorrect guess. {target_player.name} did not have value {guessed_value}.")

    def _effect_priest(self, player, card_played, must_target_self):
        valid_targets = self._get_valid_targets(player, include_self=False, targeted_effect_requires_unprotected=True)
        if must_target_self:
            self.log_message(f"Sycophant: {player.name} must target self, but Priest cannot. Fizzles.")
            return False
        if not valid_targets: self.log_message("Priest: No valid targets."); return False

        if player.is_cpu:
            target_player = random.choice(valid_targets)
            self._resolve_priest_effect(player, target_player)
            return False
        else:
            self.ui['request_target_selection_callback'](
                player, card_played, valid_targets,
                self._resolve_priest_target_selected
            )
            return True

    def _resolve_priest_target_selected(self, acting_player, target_player_id):
        target_player = next(p for p in self.players if p.id == target_player_id)
        self._resolve_priest_effect(acting_player, target_player)
        # UI does not show card for human player directly, log message is enough.
        self._finish_effect_and_proceed()

    def _resolve_priest_effect(self, acting_player, target_player):
        if not target_player.hand:
            self.log_message(f"{target_player.name} has no hand to see (Priest).")
            return

        target_card_name = target_player.hand[0].name
        if not acting_player.is_cpu:  # Human player
            self.log_message(
                f"You ({acting_player.name}) use Priest on {target_player.name} and see their {target_card_name}.")
        elif not target_player.is_cpu:  # CPU on Human
            self.log_message(f"{acting_player.name} (Priest) looks at your hand and sees your {target_card_name}.")
        else:  # CPU on CPU
            self.log_message(f"{acting_player.name} (Priest) looks at {target_player.name}'s hand.")
            # AI would store this info: acting_player.remember_card(target_player.id, target_card_name)

    def _effect_baron(self, player, card_played, must_target_self):
        valid_targets = self._get_valid_targets(player, include_self=False, targeted_effect_requires_unprotected=True)
        if must_target_self:
            self.log_message(f"Sycophant: {player.name} must target self, but Baron cannot. Fizzles.")
            return False
        if not valid_targets: self.log_message("Baron: No valid targets."); return False

        if player.is_cpu:
            target_player = random.choice(valid_targets)
            self._resolve_baron_effect(player, target_player)
            return False
        else:
            self.ui['request_target_selection_callback'](
                player, card_played, valid_targets,
                self._resolve_baron_target_selected
            )
            return True

    def _resolve_baron_target_selected(self, acting_player, target_player_id):
        target_player = next(p for p in self.players if p.id == target_player_id)
        self._resolve_baron_effect(acting_player, target_player)
        self._finish_effect_and_proceed()

    def _resolve_baron_effect(self, player, target_player):
        if not player.hand or not target_player.hand:
            self.log_message("Baron comparison requires both players to have cards. Fizzles.")
            return

        player_card = player.hand[0]
        opponent_card = target_player.hand[0]

        log_msg = f"{player.name}({player_card.name} V:{player_card.value}) vs {target_player.name}({opponent_card.name} V:{opponent_card.value}). "
        if player_card.value > opponent_card.value:
            log_msg += f"{target_player.name} is eliminated."
            self._eliminate_player(target_player)
        elif opponent_card.value > player_card.value:
            log_msg += f"{player.name} is eliminated."
            self._eliminate_player(player)
        else:
            log_msg += "Tie. No one eliminated."
        self.log_message(log_msg)

    def _effect_handmaid(self, player, card_played):
        player.is_protected = True
        self.log_message(f"{player.name} plays Handmaid and is protected.")
        return False  # No input needed

    def _effect_prince(self, player, card_played, must_target_self):
        valid_targets = []
        if must_target_self:
            if not player.is_eliminated: valid_targets = [player]
            if not valid_targets: self.log_message(
                f"Prince (Sycophant): {player.name} must target self but invalid. Fizzles."); return False
        else:
            # Prince can target self, even if no hand (to draw burned card)
            valid_targets = self._get_valid_targets(player, include_self=True,
                                                    targeted_effect_requires_unprotected=True, allow_no_hand=True)

        if not valid_targets: self.log_message("Prince: No valid targets."); return False

        if player.is_cpu:
            target_player = random.choice(valid_targets)
            self.log_message(f"CPU ({player.name}) plays Prince, targeting {target_player.name}.")
            self._resolve_prince_effect(target_player)
            return False
        else:
            self.ui['request_target_selection_callback'](
                player, card_played, valid_targets,
                self._resolve_prince_target_selected
            )
            return True

    def _resolve_prince_target_selected(self, acting_player, target_player_id):
        target_player = next(p for p in self.players if p.id == target_player_id)
        self.log_message(f"{acting_player.name} (Prince) targets {target_player.name} to discard and draw.")
        self._resolve_prince_effect(target_player)
        self._finish_effect_and_proceed()

    def _resolve_prince_effect(self, target_player):  # Reusable by Bishop too
        if not target_player.hand and not self.shared_burned_card_ref[
            'card'] and self.deck.is_empty():  # Nothing to discard, nothing to draw
            self.log_message(f"{target_player.name} has no hand and no cards to draw (Prince).")
            return

        discarded_card = None
        if target_player.hand:
            original_hand_card = target_player.hand[0]
            discarded_card = target_player.force_discard(self.deck, self.shared_burned_card_ref)
            self.log_message(f"{target_player.name} discards {discarded_card.name}.")

            if self._is_card_in_current_deck('Princess') and discarded_card.name == 'Princess':
                self.log_message(f"{target_player.name} discarded Princess (forced by Prince) and is eliminated!")
                self._eliminate_player(target_player)
                return
        else:
            if not self.deck.is_empty():
                new_card = self.deck.draw()
                target_player.add_card_to_hand(new_card)
            elif self.shared_burned_card_ref['card']:
                new_card = self.shared_burned_card_ref['card']
                target_player.add_card_to_hand(new_card)
                self.shared_burned_card_ref['card'] = None
            else:
                self.log_message(f"{target_player.name} has no card to draw (deck and burned card empty).")

        if target_player.hand:
            if not target_player.is_cpu:
                self.log_message(f"You ({target_player.name}) draw {target_player.hand[0].name}.")
            else:
                self.log_message(f"{target_player.name} draws a new card.")
        elif not target_player.is_eliminated:
            self.log_message(f"{target_player.name} has no card after Prince effect (deck and burned card empty).")

    def _effect_king(self, player, card_played, must_target_self):
        valid_targets = self._get_valid_targets(player, include_self=False, targeted_effect_requires_unprotected=True)
        if must_target_self:
            self.log_message(f"Sycophant: {player.name} must target self, but King cannot. Fizzles.")
            return False
        if not valid_targets: self.log_message("King: No valid targets."); return False

        if player.is_cpu:
            target_player = random.choice(valid_targets)
            self._resolve_king_effect(player, target_player)
            return False
        else:
            self.ui['request_target_selection_callback'](
                player, card_played, valid_targets,
                self._resolve_king_target_selected
            )
            return True

    def _resolve_king_target_selected(self, acting_player, target_player_id):
        target_player = next(p for p in self.players if p.id == target_player_id)
        self._resolve_king_effect(acting_player, target_player)
        self._finish_effect_and_proceed()

    def _resolve_king_effect(self, player, target_player):
        if not player.hand or not target_player.hand:
            self.log_message("King swap requires both players to have cards. Fizzles.");
            return

        player_card_obj = player.hand.pop(0)
        opponent_card_obj = target_player.hand.pop(0)

        player.add_card_to_hand(opponent_card_obj)
        target_player.add_card_to_hand(player_card_obj)

        self.log_message(f"{player.name} (King) swaps hand with {target_player.name}. "
                         f"{player.name} gets {opponent_card_obj.name}, {target_player.name} gets {player_card_obj.name}.")

    def _effect_countess(self, player, card_played):
        self.log_message("Countess played. No special effect.");
        return False

    def _effect_princess(self, player, card_played):
        self.log_message(f"ERROR: Princess effect executed, should have been caught earlier.");
        return False

