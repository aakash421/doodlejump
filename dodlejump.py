import pygame
import sys
import random
import os

class DoodleJump:
    def __init__(self):
        # Initialize Pygame
        pygame.init()
        self.screen_width = 1200
        self.screen_height = 800
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Doodle Jump")
        
        # Set assets path (for local testing; web deployment may need adjustments)
        self.script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else ''
        self.assets_path = os.path.join(self.script_dir, "assets")
        
        # Load assets with error handling
        self.load_assets()
        
        # Initialize font
        pygame.font.init()
        self.font = pygame.font.SysFont("Arial", 25)
        
        # Game variables
        self.score = 0
        self.playerx = self.screen_width // 2
        self.playery = 500
        self.direction = 0  # 0 for right, 1 for left
        self.jump = 0
        self.gravity = 0
        self.xmovement = 0
        self.cameray = 0
        self.platforms = [[self.screen_width // 2, 600, 0, 0]]  # [x, y, type, moving_direction]
        self.springs = []
        self.enemies = []  # [x, y, direction]
        self.projectiles = []  # [x, y, speed]
        self.game_over = False
        self.touch_left = False
        self.touch_right = False
        self.touch_shoot = False

    def create_fallback_image(self, width=70, height=10, color=(0, 255, 0)):
        """Create a fallback image (colored rectangle) if asset loading fails."""
        image = pygame.Surface((width, height), pygame.SRCALPHA)
        image.fill(color)
        return image

    def load_assets(self):
        """Load game assets with error handling and fallback."""
        self.enemy_size = 70
        asset_files = {
            "green": "green.png",
            "blue": "blue.png",
            "red": "red.png",
            "red_1": "red_1.png",
            "playerRight": "right.png",
            "playerRight_1": "right_1.png",
            "playerLeft": "left.png",
            "playerLeft_1": "left_1.png",
            "spring": "spring.png",
            "spring_1": "spring_1.png",
            "enemy": "enemy.png"
        }
        
        for attr, filename in asset_files.items():
            try:
                filepath = os.path.join(self.assets_path, filename)
                image = pygame.image.load(filepath).convert_alpha()
                if attr == "enemy":
                    image = pygame.transform.scale(image, (self.enemy_size, self.enemy_size))
                setattr(self, attr, image)
            except:
                print(f"Warning: Failed to load '{filename}'. Using fallback image.")
                if "player" in attr.lower():
                    setattr(self, attr, self.create_fallback_image(50, 50, (255, 0, 0)))
                elif "spring" in attr.lower():
                    setattr(self, attr, self.create_fallback_image(30, 20, (128, 128, 128)))
                elif "enemy" in attr.lower():
                    setattr(self, attr, self.create_fallback_image(self.enemy_size, self.enemy_size, (255, 0, 255)))
                else:
                    setattr(self, attr, self.create_fallback_image(70, 10, (0, 255, 0)))

    def updatePlayer(self):
        """Update player position and state."""
        if not self.jump:
            self.playery += self.gravity
            self.gravity += 0.5
        elif self.jump:
            self.playery -= self.jump
            self.jump -= 0.5

        # Handle keyboard and touch input
        key = pygame.key.get_pressed()
        if key[pygame.K_RIGHT] or self.touch_right:
            self.xmovement = min(self.xmovement + 0.5, 10)
            self.direction = 0
        elif key[pygame.K_LEFT] or self.touch_left:
            self.xmovement = max(self.xmovement - 0.5, -10)
            self.direction = 1
        else:
            if self.xmovement > 0:
                self.xmovement = max(self.xmovement - 0.5, 0)
            elif self.xmovement < 0:
                self.xmovement = min(self.xmovement + 0.5, 0)

        # Wrap player around screen edges
        if self.playerx > self.screen_width:
            self.playerx = -self.playerRight.get_width()
        elif self.playerx < -self.playerRight.get_width():
            self.playerx = self.screen_width

        self.playerx += self.xmovement

        # Adjust camera to follow player
        if self.playery - self.cameray < 200:
            self.cameray = max(self.cameray - 10, self.playery - 200)

        # Render player
        if not self.direction:
            image = self.playerRight_1 if self.jump else self.playerRight
        else:
            image = self.playerLeft_1 if self.jump else self.playerLeft
        self.screen.blit(image, (self.playerx, self.playery - self.cameray))

    def updatePlatforms(self):
        """Update platform positions and handle collisions."""
        player_rect = pygame.Rect(self.playerx, self.playery, self.playerRight.get_width() - 10, self.playerRight.get_height())
        for p in self.platforms:
            rect = pygame.Rect(p[0], p[1], self.green.get_width() - 10, self.green.get_height())
            if rect.colliderect(player_rect) and self.gravity > 0 and self.playery < (p[1] - self.cameray):
                if p[2] != 2:
                    self.jump = 15
                    self.gravity = 0
                else:
                    p[3] = 1

            # Move blue platforms
            if p[2] == 1:
                p[0] += 5 if p[3] == 1 else -5
                p[3] = 1 if p[0] > self.screen_width - 50 else 0 if p[0] <= 0 else p[3]

    def updateEnemies(self):
        """Update enemy positions and check collisions."""
        player_rect = pygame.Rect(self.playerx, self.playery, self.playerRight.get_width() - 10, self.playerRight.get_height())
        for e in self.enemies[:]:
            e[0] += 3 if e[2] == 1 else -3
            if e[0] > self.screen_width - self.enemy_size:
                e[2] = 0
            elif e[0] < 0:
                e[2] = 1

            enemy_rect = pygame.Rect(e[0], e[1], self.enemy_size, self.enemy_size)
            if enemy_rect.colliderect(player_rect):
                self.game_over = True

            for p in self.projectiles[:]:
                projectile_rect = pygame.Rect(p[0], p[1], 5, 10)
                if enemy_rect.colliderect(projectile_rect):
                    self.enemies.remove(e)
                    self.projectiles.remove(p)
                    self.score += 500
                    break

    def updateProjectiles(self):
        """Update projectile positions and remove off-screen projectiles."""
        for p in self.projectiles[:]:
            p[1] -= p[2]
            if p[1] < self.cameray - 100:
                self.projectiles.remove(p)
            else:
                pygame.draw.rect(self.screen, (0, 0, 255), (p[0], p[1] - self.cameray, 5, 10))

    def drawPlatforms(self):
        """Draw platforms, springs, enemies, and generate new ones."""
        for p in self.platforms[:]:
            if p[1] - self.cameray > self.screen_height:
                self.platforms.remove(p)
                platform_type = random.choices([0, 1, 2], weights=[80, 15, 5], k=1)[0]
                x = random.randint(0, self.screen_width - 70)
                y = self.platforms[-1][1] - random.randint(40, 60)
                self.platforms.append([x, y, platform_type, 0])
                self.score += 100

                if platform_type == 0 and random.randint(0, 1000) > 900:
                    self.springs.append([x, y - self.green.get_height(), 0])

                if platform_type == 0 and random.randint(0, 1000) > 950:
                    self.enemies.append([x, y - self.enemy_size, random.choice([0, 1])])

            if p[2] == 0:
                self.screen.blit(self.green, (p[0], p[1] - self.cameray))
            elif p[2] == 1:
                self.screen.blit(self.blue, (p[0], p[1] - self.cameray))
            elif p[2] == 2:
                self.screen.blit(self.red_1 if p[3] else self.red, (p[0], p[1] - self.cameray))

        for spring in self.springs[:]:
            spring_rect = pygame.Rect(spring[0], spring[1], self.spring.get_width(), self.spring.get_height())
            player_rect = pygame.Rect(self.playerx, self.playery, self.playerRight.get_width() - 10, self.playerRight.get_height())
            if spring_rect.colliderect(player_rect) and self.gravity > 0:
                self.jump = 50
                self.cameray -= 50
                spring[2] = 1
            self.screen.blit(self.spring_1 if spring[2] else self.spring, (spring[0], spring[1] - self.cameray))

        for e in self.enemies:
            self.screen.blit(self.enemy, (e[0], e[1] - self.cameray))

    def generatePlatforms(self):
        """Generate initial platforms."""
        y = self.screen_height - 200
        while y > -100:
            platform_type = random.choices([0, 1, 2], weights=[80, 15, 5], k=1)[0]
            x = random.randint(0, self.screen_width - 70)
            self.platforms.append([x, y, platform_type, 0])
            y -= random.randint(40, 60)

    def drawGrid(self):
        """Draw background grid."""
        for x in range(0, self.screen_width, 12):
            pygame.draw.line(self.screen, (222, 222, 222), (x, 0), (x, self.screen_height))
        for y in range(0, self.screen_height, 12):
            pygame.draw.line(self.screen, (222, 222, 222), (0, y), (self.screen_width, y))

    def drawGameOver(self):
        """Display game over screen."""
        game_over_text = self.font.render("Game Over! Score: " + str(self.score), True, (255, 0, 0))
        restart_text = self.font.render("Tap to Restart", True, (0, 0, 0))
        self.screen.blit(game_over_text, (self.screen_width // 2 - 100, self.screen_height // 2 - 50))
        self.screen.blit(restart_text, (self.screen_width // 2 - 100, self.screen_height // 2))

    def handleTouchInput(self):
        """Handle touch input for mobile devices."""
        self.touch_left = False
        self.touch_right = False
        self.touch_shoot = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.FINGERDOWN:
                x = event.x * self.screen_width
                y = event.y * self.screen_height
                if x < self.screen_width // 3:
                    self.touch_left = True
                elif x > 2 * self.screen_width // 3:
                    self.touch_right = True
                else:
                    self.touch_shoot = True
            if event.type == pygame.FINGERUP:
                self.touch_left = False
                self.touch_right = False
                self.touch_shoot = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and self.game_over:
                    # Reset game
                    self.score = 0
                    self.playerx = self.screen_width // 2
                    self.playery = 500
                    self.cameray = 0
                    self.jump = 0
                    self.gravity = 0
                    self.xmovement = 0
                    self.platforms = [[self.screen_width // 2, 600, 0, 0]]
                    self.springs = []
                    self.enemies = []
                    self.projectiles = []
                    self.game_over = False
                    self.generatePlatforms()
                elif event.key == pygame.K_SPACE and not self.game_over:
                    projectile_x = self.playerx + self.playerRight.get_width() // 2
                    projectile_y = self.playery
                    self.projectiles.append([projectile_x, projectile_y, 10])

    def run(self):
        """Main game loop."""
        clock = pygame.time.Clock()
        self.generatePlatforms()

        while True:
            self.screen.fill((255, 255, 255))
            clock.tick(60)

            self.handleTouchInput()

            if self.game_over:
                self.drawGameOver()
                if self.touch_shoot:  # Tap to restart
                    self.score = 0
                    self.playerx = self.screen_width // 2
                    self.playery = 500
                    self.cameray = 0
                    self.jump = 0
                    self.gravity = 0
                    self.xmovement = 0
                    self.platforms = [[self.screen_width // 2, 600, 0, 0]]
                    self.springs = []
                    self.enemies = []
                    self.projectiles = []
                    self.game_over = False
                    self.generatePlatforms()
            else:
                if self.playery - self.cameray > self.screen_height:
                    self.game_over = True
                else:
                    self.drawGrid()
                    self.drawPlatforms()
                    self.updatePlayer()
                    self.updatePlatforms()
                    self.updateEnemies()
                    self.updateProjectiles()
                    if self.touch_shoot:
                        projectile_x = self.playerx + self.playerRight.get_width() // 2
                        projectile_y = self.playery
                        self.projectiles.append([projectile_x, projectile_y, 10])
                    self.screen.blit(self.font.render(f"Score: {self.score}", True, (0, 0, 0)), (25, 25))

            pygame.display.flip()

if __name__ == "__main__":
    DoodleJump().run()