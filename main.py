"""ポケモン風の簡単なターン制バトルゲーム。"""

import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

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

COMMANDS = ["たたかう", "まもる"]
PLAYER_IMAGE_SIZE = (96, 96)


class Monster:
    """バトルに出るモンスターの情報をまとめるクラス。"""

    def __init__(self, name, max_hp, attack):
        """名前、HP、攻撃力を設定する。"""
        self.name = name
        self.max_hp = max_hp
        self.hp = max_hp
        self.attack = attack

    def take_damage(self, damage):
        """ダメージを受けてHPを減らす。"""
        self.hp -= damage
        if self.hp < 0:
            self.hp = 0


def create_new_battle():
    """新しいバトル用のプレイヤーと敵を作る。"""
    player = Monster("こうかとん", 120, 20)
    enemy = Monster("やせいモンスター", 100, 16)
    return player, enemy


def make_font(size):
    """WindowsのMS Gothicでフォントを作る。"""
    return pygame.font.SysFont("MS Gothic", size)


def load_player_image():
    """figフォルダの画像を読み込み、左右反転して返す。"""
    image_path = os.path.join(os.path.dirname(__file__), "fig", "3.png")

    try:
        image = pygame.image.load(image_path).convert_alpha()
    except (FileNotFoundError, pygame.error):
        return None

    image = pygame.transform.smoothscale(image, PLAYER_IMAGE_SIZE)
    image = pygame.transform.flip(image, True, False)
    return image


def draw_text(screen, text, font, color, x, y):
    """文字を1行だけ描画する。"""
    image = font.render(text, True, color)
    screen.blit(image, (x, y))


def draw_multiline_text(screen, text, font, color, x, y, line_height):
    """改行を含むメッセージを描画する。"""
    lines = text.split("\n")
    for i, line in enumerate(lines):
        draw_text(screen, line, font, color, x, y + i * line_height)


def draw_hp_bar(screen, x, y, width, height, hp, max_hp):
    """残りHPをバーで描画する。"""
    hp_ratio = hp / max_hp
    bar_width = int(width * hp_ratio)

    if hp_ratio > 0.5:
        hp_color = GREEN
    elif hp_ratio > 0.25:
        hp_color = ORANGE
    else:
        hp_color = RED

    pygame.draw.rect(screen, BLACK, (x, y, width, height), 2)
    pygame.draw.rect(screen, hp_color, (x, y, bar_width, height))


def draw_status_panel(screen, monster, x, y, font):
    """名前とHPを表示するパネルを描画する。"""
    pygame.draw.rect(screen, PANEL_COLOR, (x, y, 260, 95))
    pygame.draw.rect(screen, PANEL_EDGE, (x, y, 260, 95), 3)
    draw_text(screen, monster.name, font, BLACK, x + 15, y + 10)
    draw_text(screen, f"HP {monster.hp}/{monster.max_hp}", font, BLACK, x + 15, y + 40)
    draw_hp_bar(screen, x + 15, y + 68, 220, 14, monster.hp, monster.max_hp)


def draw_characters(screen, player_image):
    """プレイヤーと敵を図形で描画する。"""
    pygame.draw.ellipse(screen, ENEMY_COLOR, (555, 135, 110, 90))
    pygame.draw.ellipse(screen, BLACK, (555, 135, 110, 90), 3)
    pygame.draw.circle(screen, BLACK, (585, 170), 6)
    pygame.draw.circle(screen, BLACK, (635, 170), 6)

    if player_image is None:
        player_rect = pygame.Rect(155, 330, 90, 90)
        pygame.draw.rect(screen, PLAYER_COLOR, player_rect)
        pygame.draw.rect(screen, BLACK, player_rect, 3)
        pygame.draw.circle(screen, BLACK, (player_rect.x + 28, player_rect.y + 35), 6)
        pygame.draw.circle(screen, BLACK, (player_rect.x + 62, player_rect.y + 35), 6)
    else:
        screen.blit(player_image, (150, 315))


def draw_commands(screen, selected_command, font):
    """コマンド一覧を描画する。"""
    pygame.draw.rect(screen, PANEL_COLOR, (500, 420, 260, 105))
    pygame.draw.rect(screen, PANEL_EDGE, (500, 420, 260, 105), 3)

    for i, command in enumerate(COMMANDS):
        y = 438 + i * 38
        cursor = ">" if i == selected_command else " "
        draw_text(screen, f"{cursor} {command}", font, BLACK, 525, y)


def draw_message_box(screen, message, font):
    """現在のメッセージを表示する。"""
    pygame.draw.rect(screen, PANEL_COLOR, (40, 420, 430, 140))
    pygame.draw.rect(screen, PANEL_EDGE, (40, 420, 430, 140), 3)
    draw_multiline_text(screen, message, font, BLACK, 60, 438, 28)


def draw_battle_screen(
    screen, player, enemy, selected_command, message, font, player_image
):
    """バトル画面を描画する。"""
    screen.fill(SKY_BLUE)
    pygame.draw.rect(screen, GRASS_GREEN, (0, 385, WIDTH, 215))
    pygame.draw.ellipse(screen, (110, 170, 95), (95, 400, 230, 45))
    pygame.draw.ellipse(screen, (110, 170, 95), (515, 215, 210, 40))

    draw_status_panel(screen, enemy, 45, 35, font)
    draw_status_panel(screen, player, 490, 305, font)
    draw_characters(screen, player_image)
    draw_message_box(screen, message, font)
    draw_commands(screen, selected_command, font)


def draw_clear_screen(screen, large_font, font):
    """ゲームクリア画面を描画する。"""
    screen.fill(SKY_BLUE)
    pygame.draw.rect(screen, GRASS_GREEN, (0, 420, WIDTH, 180))
    draw_text(screen, "ゲームクリア！", large_font, BLACK, 255, 220)
    draw_text(screen, "Enterキーで終了", font, BLACK, 305, 330)


def player_action(command, player, enemy, is_protecting):
    """プレイヤーが選んだコマンドを処理する。"""
    if command == "たたかう":
        damage = random.randint(player.attack - 4, player.attack + 4)
        enemy.take_damage(damage)
        message = f"{player.name}の こうげき！\n敵に {damage} ダメージ！"
        return message, is_protecting

    if command == "まもる":
        is_protecting = True
        message = f"{player.name}は まもりを固めた！"
        return message, is_protecting

    return "コマンドを選んでください。", is_protecting


def enemy_action(player, is_protecting):
    """敵が通常攻撃か強攻撃をランダムで選んで行動する。"""
    enemy_move = random.choice(["通常攻撃", "強攻撃"])

    if enemy_move == "通常攻撃":
        damage = random.randint(12, 18)
    else:
        damage = random.randint(22, 30)

    if is_protecting:
        damage = damage // 2
        message = f"敵の{enemy_move}!\nまもりで半分にした!\n{damage} ダメージ受けた。"
    else:
        message = f"敵の{enemy_move}!\n{damage} ダメージ受けた。"

    player.take_damage(damage)
    is_protecting = False
    return message, is_protecting


def main():
    """ゲーム全体を動かすメイン関数。"""
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("ターン制モンスターバトル")
    clock = pygame.time.Clock()

    font = make_font(24)
    large_font = make_font(42)
    player_image = load_player_image()

    player, enemy = create_new_battle()
    game_state = "battle"
    selected_command = 0
    message = "コマンドを選んでください。"
    is_protecting = False

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type != pygame.KEYDOWN:
                continue

            if game_state == "battle":
                if event.key == pygame.K_UP:
                    selected_command = (selected_command - 1) % len(COMMANDS)
                elif event.key == pygame.K_DOWN:
                    selected_command = (selected_command + 1) % len(COMMANDS)
                elif event.key == pygame.K_RETURN:
                    command = COMMANDS[selected_command]
                    message, is_protecting = player_action(
                        command, player, enemy, is_protecting
                    )

                    if enemy.hp <= 0:
                        game_state = "clear"
                    else:
                        enemy_message, is_protecting = enemy_action(player, is_protecting)
                        message = message + "\n" + enemy_message

                        if player.hp <= 0:
                            game_state = "lose"
                            message = message + "\n負けました。Enterキーで終了"

            elif game_state in ["clear", "lose"] and event.key == pygame.K_RETURN:
                pygame.quit()
                sys.exit()

        if game_state in ["battle", "lose"]:
            draw_battle_screen(
                screen, player, enemy, selected_command, message, font, player_image
            )
        elif game_state == "clear":
            draw_clear_screen(screen, large_font, font)

        pygame.display.update()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
