import pygame
import random
from enum import Enum
import os

# --- Inisialisasi ---
pygame.init()
pygame.mixer.init() # Inisialisasi Mixer untuk Audio

# --- Konfigurasi Layar & Waktu ---
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60
SHIFT_DURATION = 180 # 3 Menit (dalam detik)

# --- Warna ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
DARK_GRAY = (20, 20, 20)
LIGHT_GRAY = (200, 200, 200)
GREEN = (34, 177, 76)
RED = (220, 53, 69)
YELLOW = (255, 193, 7)
BLUE = (0, 120, 215)
CARD_BG = (245, 245, 220)

class GameState(Enum):
    STORY = 1
    INSPECT = 2
    RESULT = 3
    SHIFT_END = 4
    GAME_OVER = 5

class Driver:
    def __init__(self, driver_id):
        self.id = driver_id
        self.is_villain = random.random() < 0.25 # 25% Peluang Penjahat
        self.criminal_record = ""
        
        if self.is_villain:
            img_filename = 'villain.png'
            self.name = random.choice(["Deppres", "Zarko", "Prizta", "Riko Sniper"])
            self.img_file = 'villain.png'
            self.criminal_record = random.choice([
                "PERAMPOKAN BANK UNIT 4",
                "PENYELUNDUPAN BARANG ILEGAL",
                "PENCURIAN KENDARAAN BERMOTOR",
                "PENGGELAPAN DANA NEGARA"
            ])
        else:
            img_filename = random.choice(["p1.png", "p2.png", "p3.png", "p4.png"])
            self.name = random.choice(["Budi Santoso", "Siti Aminah", "Rudi Hermawan", "Dewi Sartika"])
            self.img_file = random.choice(["p1.png", "p2.png", "p3.png", "p4.png"])
            self.criminal_record = "TIDAK ADA CATATAN KRIMINAL"

        self.plate = f"{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=2))}-{random.randint(1000, 9999)}"
        self.balance = random.randint(5000, 50000)
        self.toll_fee = 15000
        self.license_expired = random.random() < 0.2

        base_folder = os.path.dirname(os.path.abspath(__file__))
        full_img_path = os.path.join(base_folder, img_filename)

        try:
            self.photo = pygame.image.load(full_img_path).convert_alpha()
            self.photo = pygame.transform.scale(self.photo, (150, 150))
        except:
            print(f"Gagal memuat gambar: {img_filename}") # Debugging
            self.photo = pygame.Surface((150, 150))
            self.photo.fill(GRAY)

        closed_path = os.path.join(base_folder, 'gb1.png')
        open_path = os.path.join(base_folder, 'gb2.png')
        
        try:
            self.gate_closed = pygame.image.load(closed_path).convert_alpha()
            self.gate_closed = pygame.transform.scale(self.gate_closed, (720, 400 ))
        except:
            print(f"Gagal memuat gambar: gb1.png")
            self.gate_closed = pygame.Surface((400, 200))
            self.gate_closed.fill(GRAY)
        
        try:
            self.gate_open = pygame.image.load(open_path).convert_alpha()
            self.gate_open = pygame.transform.scale(self.gate_open, (720, 400))
        except:
            print(f"Gagal memuat gambar: gb2.png")
            self.gate_open = pygame.Surface((400, 200))
            self.gate_open.fill(GRAY)


    def is_approved(self):
        # Driver ditolak jika: Penjahat OR Saldo kurang OR Lisensi expired
        return not self.is_villain and self.balance >= self.toll_fee and not self.license_expired

class TollGateGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Toll Gate Guard: Frontier 2025")
        self.clock = pygame.time.Clock()
        
        # Font
        self.font_l = pygame.font.SysFont('courier', 32, bold=True)
        self.font_m = pygame.font.SysFont('arial', 22)
        self.font_s = pygame.font.SysFont('arial', 18)

        # --- SETUP AUDIO ---
        base_folder = os.path.dirname(os.path.abspath(__file__))
        
        music_path = os.path.join(base_folder, "music.ogg")

        try:
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.play(-1) 
            pygame.mixer.music.set_volume(0.5)
        except pygame.error as e:
            print(f"GAGAL MEMUAT MUSIK: {e}")
            # Opsional: Print path agar tahu dia nyari kemana
            print(f"Sistem mencoba mencari di: {music_path}")

        # Story & Typewriter Logic
        self.state = GameState.STORY
        self.story_lines = [
            "LOKASI: POS PERBATASAN SEKTOR 7...",
            "WAKTU: 18 DESEMBER 2025.",
            "EKONOMI RUNTUH. KEJAHATAN MENINGKAT.",
            "TUGAS ANDA: JAGA GERBANG INI SELAMA 3 MENIT.",
            "JANGAN BIARKAN KRIMINAL MASUK.",
            "TEKAN [SPACE] UNTUK MEMULAI SHIFT ANDA...",
            "TEKAN [A] UNTUK MENYETUJUI KENDARAAN.",
            "TEKAN [D] UNTUK MENOLAK KENDARAAN.",
            "SELAMAT BEKERJA, PETUGAS!"
        ]
        self.story_index = 0
        self.char_index = 0
        self.typewriter_speed = 2
        self.current_text = ""

        # Game Logic
        self.time_left = SHIFT_DURATION
        self.drivers_seen = 0
        self.correct_decisions = 0
        # Nyawa (Lives)
        self.max_lives = 3
        self.lives = self.max_lives
        # Animation 
        self.gate_alpha = 255
        self.show_gate_open = False
        self.animation_duration = 2.0
        self.animation_progress = 0.0
        self.is_animating = False
        self.animation_type = "none"
        self.generate_new_driver()
        self.blink_red = False
        self.last_blink_time = 0
        self.blink_interval = 200


    def generate_new_driver(self):
        self.drivers_seen += 1
        self.current_driver = Driver(self.drivers_seen)
        self.gate_alpha = 255

    def draw_id_card(self, x, y):
        # Card Body
        pygame.draw.rect(self.screen, CARD_BG, (x, y, 420, 280))
        pygame.draw.rect(self.screen, BLACK, (x, y, 420, 280), 2)
        
        # Header
        pygame.draw.rect(self.screen, BLUE, (x, y, 420, 40))
        h_text = self.font_s.render("KARTU IDENTITAS KENDARAAN", True, WHITE)
        self.screen.blit(h_text, (x + 80, y + 10))

        # Photo & Info
        self.screen.blit(self.current_driver.photo, (x + 20, y + 60))
        name_t = self.font_m.render(f"NAMA: {self.current_driver.name}", True, BLACK)
        plate_t = self.font_m.render(f"PLAT: {self.current_driver.plate}", True, BLACK)
        
        exp_color = RED if self.current_driver.license_expired else GREEN
        exp_text = "LISENSI: EXPIRED" if self.current_driver.license_expired else "LISENSI: AKTIF"
        exp_t = self.font_s.render(exp_text, True, exp_color)
        
        self.screen.blit(name_t, (x + 185, y + 70))
        self.screen.blit(plate_t, (x + 185, y + 110))
        self.screen.blit(exp_t, (x + 185, y + 150))

        # Criminal Record
        pygame.draw.rect(self.screen, LIGHT_GRAY, (x + 20, y + 220, 380, 45))
        rec_label = self.font_s.render("REKAM JEJAK:", True, BLACK)
        rec_val = self.font_s.render(self.current_driver.criminal_record, True, RED if self.current_driver.is_villain else DARK_GRAY)
        self.screen.blit(rec_label, (x + 30, y + 225))
        self.screen.blit(rec_val, (x + 30, y + 242))

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return False
            if event.type == pygame.KEYDOWN:
                if self.state == GameState.STORY:
                    if event.key == pygame.K_SPACE:
                        if self.char_index < len(self.story_lines[self.story_index]):
                            self.char_index = len(self.story_lines[self.story_index])
                        else:
                            self.story_index += 1
                            self.char_index = 0
                            if self.story_index >= len(self.story_lines):
                                self.state = GameState.INSPECT
                            
                elif self.state == GameState.INSPECT and self.gate_alpha <= 0:
                    if event.key == pygame.K_a: self.submit_decision(True)
                    if event.key == pygame.K_d: self.submit_decision(False)
                elif self.state == GameState.GAME_OVER:
                    if event.key == pygame.K_r:
                        self.reset_game()
        return True

    def reset_game(self):
        self.time_left = SHIFT_DURATION
        self.drivers_seen = 0
        self.correct_decisions = 0
        self.lives = self.max_lives
        self.story_index = 0
        self.char_index = 0
        self.state = GameState.STORY
        self.generate_new_driver()
        # Musik tidak perlu direset karena loop terus

    def submit_decision(self, approved):
        is_correct = (approved == self.current_driver.is_approved())
        if is_correct:
            self.correct_decisions += 1
        else:
            self.lives -= 1

        if is_correct and approved:
            self.result_msg = "AKSES DIBERIKAN"
            self.animation_type = "approve_correct"
        elif is_correct and not approved:
            self.result_msg = "AKSES DITOLAK"
            self.animation_type = "deny_correct" 
        else:
            if self.lives <= 0:
                self.result_msg = "ANDA DIPECAT!"
                self.result_color = RED
                self.show_gate_open = False
                self.state = GameState.GAME_OVER
                return
            else:
                self.result_msg = "KESALAHAN FATAL!"
                self.animation_type = "incorrect"
                
        
        self.result_color = GREEN if is_correct else RED
        self.show_gate_open = is_correct and approved
        self.state = GameState.RESULT
        self.result_timer = 2.0
        self.animation_progress = 0.0
        self.is_animating = True

    def update(self, dt):
        if self.state == GameState.STORY:
            if self.char_index < len(self.story_lines[self.story_index]):
                self.char_index += 0.5

        elif self.state == GameState.INSPECT:
            self.time_left -= dt
            if self.gate_alpha > 0: self.gate_alpha -= 5
            if self.time_left <= 0: self.state = GameState.SHIFT_END
        
        elif self.state == GameState.RESULT:
            self.result_timer -= dt
            if self.is_animating:
                self.animation_progress += dt / self.animation_duration
                if self.animation_progress >= 1.0:
                    self.animation_progress = 1.0
                    self.is_animating = False
            if self.result_timer <= 0:
                self.generate_new_driver()
                self.state = GameState.INSPECT
            if self.animation_type == "incorrect":
                current_time = pygame.time.get_ticks()
                if current_time - self.last_blink_time >= self.blink_interval:
                    self.blink_red = not self.blink_red
                    self.last_blink_time = current_time #Timer blink anim 

    def draw(self):
        self.screen.fill(BLACK)

        if self.state == GameState.STORY:
            line = self.story_lines[self.story_index]
            self.current_text = line[:int(self.char_index)]
            txt = self.font_l.render(self.current_text, True, GREEN)
            self.screen.blit(txt, (100, SCREEN_HEIGHT//2))
            
        elif self.state == GameState.INSPECT:
            self.screen.fill(DARK_GRAY)
            self.draw_id_card(150, 230)
            
            # Database Panel
            pygame.draw.rect(self.screen, LIGHT_GRAY, (700, 230, 350, 280))
            self.screen.blit(self.font_m.render("SISTEM PEMBAYARAN", True, BLACK), (720, 240))
            bal_color = RED if self.current_driver.balance < 15000 else BLACK
            bal_t = self.font_m.render(f"SALDO: Rp {self.current_driver.balance:,}", True, bal_color)
            self.screen.blit(bal_t, (720, 300))
            self.screen.blit(self.font_s.render("TARIF MINIMAL: Rp 15.000", True, BLACK), (720, 340))

            # Timer & Score
            timer_t = self.font_l.render(f"SISA WAKTU: {int(self.time_left)}s", True, YELLOW)
            self.screen.blit(timer_t, (SCREEN_WIDTH//2 - 150, 50))
            score_t = self.font_m.render(f"BENAR: {self.correct_decisions}", True, WHITE)
            self.screen.blit(score_t, (20, 20))

            # Life Bar
            bar_x = SCREEN_WIDTH - 350
            bar_y = 20
            bar_w = 300
            bar_h = 28
            
            # Background Bar
            pygame.draw.rect(self.screen, LIGHT_GRAY, (bar_x, bar_y, bar_w, bar_h))
            # Filled Bar
            fill_w = int((self.lives / self.max_lives) * (bar_w - 4))
            if fill_w > 0:
                pygame.draw.rect(self.screen, RED, (bar_x + 2, bar_y + 2, fill_w, bar_h - 4))
            # Border
            pygame.draw.rect(self.screen, BLACK, (bar_x, bar_y, bar_w, bar_h), 2)
            
            life_t = self.font_s.render(f"NYAWA: {self.lives}/{self.max_lives}", True, BLACK)
            self.screen.blit(life_t, (bar_x + 8, bar_y + 4))

            # Fade In Gerbang
            if self.gate_alpha > 0:
                fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                fade_surface.fill(BLACK)
                fade_surface.set_alpha(self.gate_alpha)
                self.screen.blit(fade_surface, (0, 0))

        elif self.state == GameState.RESULT:
            self.screen.blit(self.font_l.render(self.result_msg, True, self.result_color), (SCREEN_WIDTH//2-150, 100))
            life_t = self.font_m.render(f"NYAWA: {self.lives}/{self.max_lives}", True, WHITE)
            self.screen.blit(life_t, (SCREEN_WIDTH//2-80, 180))

            if self.is_animating or self.animation_progress > 0:
                gate_x = SCREEN_WIDTH // 2 - 350
                gate_y = 300

                if self.animation_type == "approve_correct":
                    if self.animation_progress < 0.5:
                        closed_alpha = int(255 * (1.0 - self.animation_progress * 2))
                        open_alpha = int(255 * (self.animation_progress * 2))
                    else:
                        closed_alpha = 0
                        open_alpha = int(255 * (1.0 - (self.animation_progress - 0.5) * 2))
                    
                    closed_surf = self.current_driver.gate_closed.copy()
                    closed_surf.set_alpha(closed_alpha)
                    open_surf = self.current_driver.gate_open.copy()
                    open_surf.set_alpha(open_alpha)

                    self.screen.blit(closed_surf, (gate_x, gate_y))
                    self.screen.blit(open_surf, (gate_x, gate_y))

                elif self.animation_type == "deny_correct":
                    alpha = int(255 * (1.0 - self.animation_progress))
                    closed_surf = self.current_driver.gate_closed.copy()
                    closed_surf.set_alpha(alpha)
                    self.screen.blit(closed_surf, (gate_x, gate_y))
                
                elif self.animation_type == "incorrect":
                    if self.blink_red:
                        red_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                        red_overlay.fill(RED)
                        red_overlay.set_alpha(128)
                        self.screen.blit(red_overlay, (0, 0))
        
        elif self.state == GameState.SHIFT_END:
            self.screen.blit(self.font_l.render("SHIFT SELESAI", True, YELLOW), (SCREEN_WIDTH//2-100, 300))
            res = self.font_m.render(f"Total Keputusan Benar: {self.correct_decisions}", True, WHITE)
            self.screen.blit(res, (SCREEN_WIDTH//2-120, 400))

        elif self.state == GameState.GAME_OVER:
            self.screen.fill(DARK_GRAY)
            self.screen.blit(self.font_l.render("GAME OVER - ANDA DIPECAT", True, RED), (SCREEN_WIDTH//2-260, 250))
            res = self.font_m.render(f"Keputusan Benar: {self.correct_decisions}", True, WHITE)
            self.screen.blit(res, (SCREEN_WIDTH//2-100, 330))
            self.screen.blit(self.font_s.render("Tekan [R] untuk mencoba lagi", True, LIGHT_GRAY), (SCREEN_WIDTH//2-110, 380))
            
            life_t = self.font_m.render(f"NYAWA: {self.lives}/{self.max_lives}", True, WHITE)
            self.screen.blit(life_t, (SCREEN_WIDTH//2-60, 360))

        pygame.display.flip()

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            running = self.handle_input()
            self.update(dt)
            self.draw()
        pygame.quit()

if __name__ == "__main__":
    game = TollGateGame()
    game.run()