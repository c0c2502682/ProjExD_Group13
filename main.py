"""ポケモン風の簡単なターン制バトルゲーム。"""

import array
import math
import os
import random
import sys

import pygame


WIDTH = 800
HEIGHT = 600
FPS = 60

BLACK = (30, 30, 30)
SKY_BLUE = (190, 225, 245)
GRASS_GREEN = (95, 180, 105)
PANEL_COLOR = (250, 248, 230)
PANEL_EDGE = (70, 70, 70)
PLAYER_COLOR = (80, 140, 240)
ENEMY_COLOR = (130, 210, 110)
RED = (230, 80, 70)
ORANGE = (240, 160, 65)
GREEN = (80, 190, 100)

COMMANDS = ["たたかう", "まもる", "メガシンカ", "ひっさつわざ"]
PLAYER_IMAGE_SIZE = (180, 180)
ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fig")
ORIGINAL_PLAYER_IMAGE_PATH = os.path.join(ASSET_DIR, "3.png")
PLAYER_IMAGE_PATH = os.path.join(ASSET_DIR, "player.png")
ENEMY_IMAGE_PATH = os.path.join(ASSET_DIR, "enemy.png")
BACKGROUND_IMAGE_PATH = os.path.join(ASSET_DIR, "background.png")


class Monster:
    """バトルに出るモンスターの情報をまとめるクラス。"""

    def __init__(self, name: str, max_hp: int, attack: int):
        """名前、HP、攻撃力を設定する。"""
        self.name = name
        self.max_hp = max_hp
        self.hp = max_hp
        self.attack = attack

    def take_damage(self, damage: int):
        """ダメージを受けてHPを減らす。"""
        self.hp -= damage
        if self.hp < 0:
            self.hp = 0


def create_new_battle() -> tuple[Monster, Monster]:
    """新しいバトル用のプレイヤーと敵を作る。"""
    player = Monster("こうかとん", 120, 20)
    enemy = Monster("やせいモンスター", 100, 16)
    return player, enemy


def make_font(size: int) -> pygame.font.Font:
    """WindowsのMS Gothicでフォントを作る。"""
    return pygame.font.SysFont("MS Gothic", size)


def create_sprite(size: tuple[int, int], color: tuple[int, int, int], accent_color: tuple[int, int, int] = None) -> pygame.Surface:
    """簡単な見た目用のスプライトを作る。"""
    surface = pygame.Surface(size, pygame.SRCALPHA)
    surface.fill((0, 0, 0, 0))
    pygame.draw.rect(surface, color, (8, 8, size[0] - 16, size[1] - 16), border_radius=18)
    if accent_color is not None:
        pygame.draw.circle(surface, accent_color, (size[0] // 2, size[1] // 2), 40)
    return surface


def ensure_assets():
    """必要な画像をfigフォルダに作成または用意する。"""
    os.makedirs(ASSET_DIR, exist_ok=True)

    if os.path.exists(ORIGINAL_PLAYER_IMAGE_PATH):
        if not os.path.exists(PLAYER_IMAGE_PATH):
            pygame.image.save(pygame.image.load(ORIGINAL_PLAYER_IMAGE_PATH).convert_alpha(), PLAYER_IMAGE_PATH)
    else:
        if not os.path.exists(PLAYER_IMAGE_PATH):
            player_surface = create_sprite(PLAYER_IMAGE_SIZE, (80, 140, 240), (250, 220, 90))
            pygame.image.save(player_surface, PLAYER_IMAGE_PATH)

    if not os.path.exists(ENEMY_IMAGE_PATH):
        enemy_surface = create_sprite(PLAYER_IMAGE_SIZE, (130, 210, 110), (240, 80, 70))
        pygame.image.save(enemy_surface, ENEMY_IMAGE_PATH)

    if not os.path.exists(BACKGROUND_IMAGE_PATH):
        bg = pygame.Surface((WIDTH, HEIGHT))
        bg.fill(SKY_BLUE)
        pygame.draw.rect(bg, GRASS_GREEN, (0, 385, WIDTH, 215))
        pygame.draw.ellipse(bg, (110, 170, 95), (95, 400, 230, 45))
        pygame.draw.ellipse(bg, (110, 170, 95), (515, 215, 210, 40))
        pygame.image.save(bg, BACKGROUND_IMAGE_PATH)


def make_tone_sound(frequency: int, duration: float, volume: float = 0.25) -> pygame.mixer.Sound:
    """簡単な音声を作る。"""
    sample_rate = 22050
    n_samples = int(sample_rate * duration)
    data = array.array("h")
    for i in range(n_samples):
        value = int(32767 * math.sin(2 * math.pi * frequency * i / sample_rate) * volume)
        data.append(value)
    sound = pygame.mixer.Sound(buffer=data.tobytes())
    sound.set_volume(volume)
    return sound


def init_sound_bank() -> dict:
    """効果音のバンクを作る。"""
    try:
        pygame.mixer.init(frequency=22050, size=-16, channels=2)
    except pygame.error:
        return {}

    return {
        "attack": make_tone_sound(660, 0.12, 0.18),
        "defend": make_tone_sound(440, 0.14, 0.12),
        "win": make_tone_sound(880, 0.2, 0.16),
    }


def load_player_image() -> pygame.Surface:
    """プレイヤー画像を読み込む。失敗時は必ず描画可能な画像を返す。"""
    for path in [PLAYER_IMAGE_PATH, ORIGINAL_PLAYER_IMAGE_PATH]:
        if os.path.exists(path):
            try:
                image = pygame.image.load(path).convert_alpha()
                return pygame.transform.smoothscale(image, PLAYER_IMAGE_SIZE)
            except (FileNotFoundError, pygame.error):
                continue
    fallback = create_sprite(PLAYER_IMAGE_SIZE, PLAYER_COLOR, (255, 220, 90))
    return fallback


def load_enemy_image() -> pygame.Surface:
    """敵画像を読み込む。失敗時は必ず描画可能な画像を返す。"""
    try:
        image = pygame.image.load(ENEMY_IMAGE_PATH).convert_alpha()
        return pygame.transform.smoothscale(image, PLAYER_IMAGE_SIZE)
    except (FileNotFoundError, pygame.error):
        return create_sprite(PLAYER_IMAGE_SIZE, ENEMY_COLOR, (240, 80, 70))


def load_background_image() -> pygame.Surface:
    """背景画像を読み込む。"""
    try:
        return pygame.image.load(BACKGROUND_IMAGE_PATH).convert()
    except (FileNotFoundError, pygame.error):
        return None


def draw_text(screen: pygame.Surface, text: str, font: pygame.font.Font, color: tuple[int, int, int], x: int, y: int):
    """文字を1行だけ描画する。"""
    image = font.render(text, True, color)
    screen.blit(image, (x, y))


def draw_multiline_text(screen: pygame.Surface, text: str, font: pygame.font.Font, color: tuple[int, int, int], x: int, y: int, line_height: int):
    """改行を含むメッセージを描画する。"""
    lines = text.split("\n")
    for i, line in enumerate(lines):
        draw_text(screen, line, font, color, x, y + i * line_height)


def draw_hp_bar(screen: pygame.Surface, x: int, y: int, width: int, height: int, hp: int, max_hp: int):
    """残りHPをバーで描画する。"""
    hp_ratio = hp / max_hp if max_hp > 0 else 0
    bar_width = int(width * hp_ratio)

    if hp_ratio > 0.5:
        hp_color = GREEN
    elif hp_ratio > 0.25:
        hp_color = ORANGE
    else:
        hp_color = RED

    pygame.draw.rect(screen, BLACK, (x, y, width, height), 2)
    pygame.draw.rect(screen, hp_color, (x, y, bar_width, height))


def draw_status_panel(screen: pygame.Surface, monster: Monster, x: int, y: int, font: pygame.font.Font):
    """名前とHPを表示するパネルを描画する。"""
    pygame.draw.rect(screen, PANEL_COLOR, (x, y, 260, 95))
    pygame.draw.rect(screen, PANEL_EDGE, (x, y, 260, 95), 3)
    draw_text(screen, monster.name, font, BLACK, x + 15, y + 10)
    draw_text(screen, f"HP {monster.hp}/{monster.max_hp}", font, BLACK, x + 15, y + 40)
    draw_hp_bar(screen, x + 15, y + 68, 220, 14, monster.hp, monster.max_hp)


def draw_characters(screen: pygame.Surface, player_image: pygame.Surface, enemy_image: pygame.Surface):
    """プレイヤーと敵を描画する。"""
    pygame.draw.rect(screen, (255, 255, 255), (70, 240, 180, 180), border_radius=20)
    pygame.draw.rect(screen, (255, 255, 255), (520, 110, 180, 180), border_radius=20)
    if enemy_image is not None:
        screen.blit(enemy_image, (520, 110))
    if player_image is not None:
        screen.blit(player_image, (70, 240))


def draw_commands(screen: pygame.Surface, selected_command: int, font: pygame.font.Font):
    """コマンド一覧を描画する。"""
    pygame.draw.rect(screen, PANEL_COLOR, (500, 420, 260, 150))
    pygame.draw.rect(screen, PANEL_EDGE, (500, 420, 260, 150), 3)

    for i, command in enumerate(COMMANDS):
        y = 438 + i * 32
        cursor = ">" if i == selected_command else " "
        draw_text(screen, f"{cursor} {command}", font, BLACK, 525, y)


def draw_message_box(screen: pygame.Surface, message: str, font: pygame.font.Font):
    """現在のメッセージを表示する。"""
    pygame.draw.rect(screen, PANEL_COLOR, (40, 420, 430, 140))
    pygame.draw.rect(screen, PANEL_EDGE, (40, 420, 430, 140), 3)
    draw_multiline_text(screen, message, font, BLACK, 60, 438, 28)


def draw_title_screen(screen: pygame.Surface, large_font: pygame.font.Font, font: pygame.font.Font, background_image: pygame.Surface, player_image: pygame.Surface):
    """タイトル画面を描画する。"""
    if background_image is not None:
        screen.blit(background_image, (0, 0))
    else:
        screen.fill(SKY_BLUE)
    pygame.draw.rect(screen, PANEL_COLOR, (140, 150, 520, 270))
    pygame.draw.rect(screen, PANEL_EDGE, (140, 150, 520, 270), 4)
    if player_image is not None:
        screen.blit(player_image, (310, 170))
    draw_text(screen, "こうかとんモンスターバトル", large_font, BLACK, 150, 360)
    draw_text(screen, "Enterキーでスタート", font, BLACK, 285, 430)


def draw_clear_screen(screen: pygame.Surface, large_font: pygame.font.Font, font: pygame.font.Font, background_image: pygame.Surface):
    """ゲームクリア画面を描画する。"""
    if background_image is not None:
        screen.blit(background_image, (0, 0))
    else:
        screen.fill(SKY_BLUE)
    pygame.draw.rect(screen, PANEL_COLOR, (190, 190, 420, 170))
    pygame.draw.rect(screen, PANEL_EDGE, (190, 190, 420, 170), 4)
    draw_text(screen, "ゲームクリア！", large_font, BLACK, 245, 225)
    draw_text(screen, "Enterキーで終了", font, BLACK, 285, 300)


def draw_gameover_screen(screen: pygame.Surface, large_font: pygame.font.Font, font: pygame.font.Font, background_image: pygame.Surface):
    """ゲームオーバー画面を描画する。"""
    if background_image is not None:
        screen.blit(background_image, (0, 0))
    else:
        screen.fill(SKY_BLUE)
    pygame.draw.rect(screen, PANEL_COLOR, (190, 190, 420, 170))
    pygame.draw.rect(screen, PANEL_EDGE, (190, 190, 420, 170), 4)
    draw_text(screen, "ゲームオーバー", large_font, BLACK, 240, 225)
    draw_text(screen, "Enterキーで終了", font, BLACK, 285, 300)


def draw_battle_screen(screen: pygame.Surface, player: Monster, enemy: Monster, selected_command: int, message: str, font: pygame.font.Font, player_image: pygame.Surface, enemy_image: pygame.Surface, background_image: pygame.Surface):
    """バトル画面を描画する。"""
    if background_image is not None:
        screen.blit(background_image, (0, 0))
    else:
        screen.fill(SKY_BLUE)

    draw_status_panel(screen, enemy, 45, 35, font)
    draw_status_panel(screen, player, 490, 305, font)
    draw_characters(screen, player_image, enemy_image)
    draw_message_box(screen, message, font)
    draw_commands(screen, selected_command, font)


def player_action(command: str, player: Monster, enemy: Monster, is_protecting: bool, mega_used: bool, sound_bank: dict) -> tuple[str, bool, bool]:
    """プレイヤーが選んだコマンドを処理する。"""
    if command == "たたかう":
        damage = random.randint(player.attack - 4, player.attack + 4)
        enemy.take_damage(damage)
        if sound_bank:
            sound_bank["attack"].play()
        message = f"{player.name}の こうげき！\n敵に {damage} ダメージ！"
        return message, is_protecting, mega_used

    if command == "まもる":
        if sound_bank:
            sound_bank["defend"].play()
        is_protecting = True
        message = f"{player.name}は まもりを固めた！"
        return message, is_protecting, mega_used

    if command == "メガシンカ" and not mega_used:
        player.attack += 10
        mega_used = True
        if sound_bank:
            sound_bank["win"].play()
        message = f"{player.name}は メガシンカ！\n攻撃力が上がった！"
        return message, is_protecting, mega_used

    if command == "メガシンカ" and mega_used:
        message = "メガシンカは もう使えない！"
        return message, is_protecting, mega_used

    if command == "ひっさつわざ":
        damage = random.randint(28, 38)
        enemy.take_damage(damage)
        if sound_bank:
            sound_bank["attack"].play()
        message = f"{player.name}の ひっさつわざ！\n敵に {damage} ダメージ！"
        return message, is_protecting, mega_used

    return "コマンドを選んでください。", is_protecting, mega_used


def enemy_action(player: Monster, is_protecting: bool, sound_bank: dict) -> tuple[str, bool]:
    """
    敵がランダムな行動（通常攻撃、強攻撃、まもる）を選択して実行する関数。
    
    Args:
        player (Monster): プレイヤーのオブジェクト
        is_protecting (bool): プレイヤーが守り状態かどうか
        sound_bank (dict): 効果音の辞書
        
    Returns:
        tuple[str, bool]: (バトルログのメッセージ, 新しいプレイヤーの守り状態)
    """
    enemy_move = random.choice(["通常攻撃", "強攻撃", "まもる"])
    message = ""

    if enemy_move == "まもる":
        if sound_bank:
            sound_bank["defend"].play()
        message = "敵はやせいの まもりを固めた！"
        return message, is_protecting

    if enemy_move == "通常攻撃":
        damage = random.randint(12, 18)
    else:  # 強攻撃
        damage = random.randint(22, 30)

    if is_protecting:
        if sound_bank:
            sound_bank["attack"].play()
        damage = damage // 2
        message = f"敵の {enemy_move}！\nこうかとんは身を守っている！\n{damage} ダメージ受けた。"
        player.take_damage(damage)
        return message, False
    else:
        if sound_bank:
            sound_bank["attack"].play()
        message = f"敵の {enemy_move}！\nこうかとんに {damage} ダメージ！"
        player.take_damage(damage)
        return message, False


def main():
    """ゲーム全体を動かすメイン関数。"""
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("ターン制モンスターバトル")
    clock = pygame.time.Clock()

    font = make_font(24)
    large_font = make_font(42)
    ensure_assets()
    player_image = load_player_image()
    enemy_image = load_enemy_image()
    background_image = load_background_image()
    sound_bank = init_sound_bank()

    player, enemy = create_new_battle()
    game_state = "title"
    selected_command = 0
    message = "Enterキーでスタート"
    is_protecting = False
    mega_used = False

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type != pygame.KEYDOWN:
                continue

            if game_state == "title":
                if event.key == pygame.K_RETURN:
                    game_state = "battle"
                    message = "コマンドを選んでください。"
                continue

            if game_state == "battle":
                if event.key == pygame.K_UP:
                    selected_command = (selected_command - 1) % len(COMMANDS)
                elif event.key == pygame.K_DOWN:
                    selected_command = (selected_command + 1) % len(COMMANDS)
                elif event.key == pygame.K_RETURN:
                    command = COMMANDS[selected_command]
                    message, is_protecting, mega_used = player_action(
                        command, player, enemy, is_protecting, mega_used, sound_bank
                    )

                    if enemy.hp <= 0:
                        game_state = "clear"
                        message = "勝利！"
                        if sound_bank:
                            sound_bank["win"].play()
                    else:
                        enemy_message, is_protecting = enemy_action(player, is_protecting, sound_bank)
                        message = message + "\n" + enemy_message

                        if player.hp <= 0:
                            game_state = "gameover"
                            message = "負けました。Enterキーで終了"

            elif game_state in ["clear", "gameover"] and event.key == pygame.K_RETURN:
                pygame.quit()
                sys.exit()

        if game_state == "title":
            draw_title_screen(screen, large_font, font, background_image, player_image)
        elif game_state == "battle":
            draw_battle_screen(
                screen,
                player,
                enemy,
                selected_command,
                message,
                font,
                player_image,
                enemy_image,
                background_image,
            )
        elif game_state == "clear":
            draw_clear_screen(screen, large_font, font, background_image)
        elif game_state == "gameover":
            draw_gameover_screen(screen, large_font, font, background_image)

        pygame.display.update()
        clock.tick(FPS)


if __name__ == "__main__":
    main()