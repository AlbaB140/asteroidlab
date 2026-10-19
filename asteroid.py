import pygame
import random
import math

pygame.init()

width = 800
height = 600
fps = 60

num_asteroids = 6
num_enemies = 3
rotation_speed = 3

thrust = 0.15
drag = 0.99
max_speed = 7
missile_speed = 8

min_child_radius = 10
split_scale = 0.6

enemy_wander_speed = 1.5
enemy_attack_speed = 3.5
enemy_turn_speed = 3

player_start_lives = 3
invulnerable_frames = 90

fov_angle = 50
fov_radius = 220


def normalize_angle(angle):
    return (angle + 180) % 360 - 180


screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("asteroid lab")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 25)
big_font = pygame.font.Font(None, 64)


class Spaceship:
    def __init__(self, x, y):
        self.position = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(0, 0)
        self.acceleration = pygame.Vector2(0, 0)
        self.angle = 90
        self.radius = 18
        self.is_thrusting = False
        self.lives = player_start_lives
        self.invulnerable_timer = 0

    def get_forward_vector(self):
        radians = math.radians(self.angle)
        return pygame.Vector2(math.cos(radians), -math.sin(radians))

    def update(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.angle += rotation_speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.angle -= rotation_speed

        forward = self.get_forward_vector()

        self.acceleration = pygame.Vector2(0, 0)
        self.is_thrusting = False

        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.acceleration = forward * thrust
            self.is_thrusting = True

        self.velocity += self.acceleration
        self.velocity *= drag

        if self.velocity.length() > max_speed:
            self.velocity.scale_to_length(max_speed)

        self.position += self.velocity

        if self.position.x > width:
            self.position.x = 0
        if self.position.x < 0:
            self.position.x = width
        if self.position.y > height:
            self.position.y = 0
        if self.position.y < 0:
            self.position.y = height

        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= 1

    def hit(self):
        if self.invulnerable_timer > 0:
            return
        self.lives -= 1
        self.invulnerable_timer = invulnerable_frames
        self.position = pygame.Vector2(width / 2, height / 2)
        self.velocity = pygame.Vector2(0, 0)

    def draw(self):
        if self.invulnerable_timer > 0 and (self.invulnerable_timer // 5) % 2 == 0:
            return

        forward = self.get_forward_vector()
        left = forward.rotate(140)
        right = forward.rotate(-140)

        front = self.position + forward * 22
        back_left = self.position + left * 17
        back_right = self.position + right * 17

        pygame.draw.polygon(screen, (80, 255, 150), [front, back_left, back_right], 2)
        pygame.draw.circle(screen, (80, 255, 150), (int(self.position.x), int(self.position.y)), 3)

        if self.is_thrusting:
            flame_position = self.position - forward * 20
            pygame.draw.circle(screen, (255, 140, 50), (int(flame_position.x), int(flame_position.y)), 5)

    def draw_forward_vector(self):
        forward = self.get_forward_vector()
        end_point = self.position + forward * 60
        pygame.draw.line(screen, (255, 80, 80), self.position, end_point, 2)

    def draw_velocity_vector(self):
        if self.velocity.length() > 0.1:
            end_point = self.position + self.velocity * 10
            pygame.draw.line(screen, (80, 180, 255), self.position, end_point, 3)


class EnemyShip:
    def __init__(self, x=None, y=None):
        if x is None or y is None:
            x = random.randint(40, width - 40)
            y = random.randint(40, height - 40)

        self.position = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(0, 0)
        self.angle = random.uniform(0, 360)
        self.radius = 16
        self.fov_angle = fov_angle
        self.fov_radius = fov_radius
        self.sees_player = False

    def get_forward_vector(self):
        radians = math.radians(self.angle)
        return pygame.Vector2(math.cos(radians), -math.sin(radians))

    def update(self):
        if not self.sees_player:
            self.angle += random.uniform(-2, 2)
            self.velocity = self.get_forward_vector() * enemy_wander_speed

        self.position += self.velocity

        if self.position.x > width + self.radius:
            self.position.x = -self.radius
        if self.position.x < -self.radius:
            self.position.x = width + self.radius
        if self.position.y > height + self.radius:
            self.position.y = -self.radius
        if self.position.y < -self.radius:
            self.position.y = height + self.radius

    def update_fov(self, player):
        forward = self.get_forward_vector()
        to_player = player.position - self.position
        distance = to_player.length()

        if distance == 0 or distance > self.fov_radius:
            self.sees_player = False
            return

        angle_diff = abs(normalize_angle(forward.angle_to(to_player)))
        self.sees_player = angle_diff <= self.fov_angle / 2

    def attack(self, player):
        to_player = player.position - self.position
        if to_player.length() == 0:
            return

        forward = self.get_forward_vector()
        turn_needed = normalize_angle(forward.angle_to(to_player))
        turn = max(-enemy_turn_speed, min(enemy_turn_speed, turn_needed))
        self.angle += turn

        self.velocity = self.get_forward_vector() * enemy_attack_speed

    def draw_fov(self):
        forward = self.get_forward_vector()
        left_edge = forward.rotate(-self.fov_angle / 2) * self.fov_radius
        right_edge = forward.rotate(self.fov_angle / 2) * self.fov_radius
        color = (255, 80, 80) if self.sees_player else (90, 90, 110)

        pygame.draw.line(screen, color, self.position, self.position + left_edge, 1)
        pygame.draw.line(screen, color, self.position, self.position + right_edge, 1)

    def draw(self):
        forward = self.get_forward_vector()
        left = forward.rotate(140)
        right = forward.rotate(-140)

        front = self.position + forward * 18
        back_left = self.position + left * 14
        back_right = self.position + right * 14

        color = (255, 80, 80) if self.sees_player else (255, 140, 50)
        pygame.draw.polygon(screen, color, [front, back_left, back_right], 2)


class Asteroid:
    def __init__(self, radius=None, position=None, velocity=None):
        self.radius = radius if radius is not None else random.randint(28, 40)

        if position is not None:
            self.position = pygame.Vector2(position)
        else:
            self.position = pygame.Vector2(
                random.randint(self.radius, width - self.radius),
                random.randint(self.radius, height - self.radius)
            )

        if velocity is not None:
            self.velocity = pygame.Vector2(velocity)
        else:
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1.0, 2.5)
            self.velocity = pygame.Vector2(math.cos(angle), math.sin(angle)) * speed

    def update(self):
        self.position += self.velocity

        if self.position.x > width + self.radius:
            self.position.x = -self.radius
        if self.position.x < -self.radius:
            self.position.x = width + self.radius
        if self.position.y > height + self.radius:
            self.position.y = -self.radius
        if self.position.y < -self.radius:
            self.position.y = height + self.radius

    def draw(self):
        pygame.draw.circle(screen, (170, 170, 170), (int(self.position.x), int(self.position.y)), self.radius, 2)


class Missile:
    def __init__(self, start_position, direction):
        self.position = pygame.Vector2(start_position)
        self.radius = 4
        self.velocity = direction * missile_speed

    def update(self):
        self.position += self.velocity

    def draw(self):
        pygame.draw.circle(screen, (255, 230, 80), (int(self.position.x), int(self.position.y)), self.radius)

    def is_off_screen(self):
        return (
            self.position.x < 0
            or self.position.x > width
            or self.position.y < 0
            or self.position.y > height
        )


def missile_hits(missile, target):
    distance = missile.position.distance_to(target.position)
    return distance < missile.radius + target.radius


def split_asteroid(asteroid):
    new_radius = int(asteroid.radius * split_scale)
    if new_radius < min_child_radius:
        return []

    children = []
    if asteroid.velocity.length() > 0.01:
        base_direction = asteroid.velocity.normalize()
    else:
        base_direction = pygame.Vector2(1, 0)

    for offset in (-45, 45):
        direction = base_direction.rotate(offset + random.uniform(-10, 10))
        speed = random.uniform(1.5, 3.0)
        children.append(
            Asteroid(
                radius=new_radius,
                position=asteroid.position.copy(),
                velocity=direction * speed
            )
        )

    return children


def resolve_asteroid_collisions(asteroids):
    for i in range(len(asteroids)):
        for j in range(i + 1, len(asteroids)):
            a = asteroids[i]
            b = asteroids[j]

            delta = a.position - b.position
            distance = delta.length()

            if distance == 0 or distance > a.radius + b.radius:
                continue

            overlap = a.radius + b.radius - distance
            normal = delta / distance

            mass_a = a.radius
            mass_b = b.radius
            total_mass = mass_a + mass_b

            a.position += normal * overlap * (mass_b / total_mass)
            b.position -= normal * overlap * (mass_a / total_mass)

            a.velocity, b.velocity = b.velocity, a.velocity


def player_is_hit(player, asteroids, enemies):
    for asteroid in asteroids:
        if player.position.distance_to(asteroid.position) < player.radius + asteroid.radius:
            return True
    for enemy in enemies:
        if player.position.distance_to(enemy.position) < player.radius + enemy.radius:
            return True
    return False


player = Spaceship(width / 2, height / 2)
asteroids = [Asteroid() for _ in range(num_asteroids)]
enemies = [EnemyShip() for _ in range(num_enemies)]
missiles = []
score = 0
game_over = False

running = True

while running:
    clock.tick(fps)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if game_over and event.key == pygame.K_r:
                player = Spaceship(width / 2, height / 2)
                asteroids = [Asteroid() for _ in range(num_asteroids)]
                enemies = [EnemyShip() for _ in range(num_enemies)]
                missiles = []
                score = 0
                game_over = False
            elif not game_over and event.key == pygame.K_SPACE:
                forward = player.get_forward_vector()
                missile_start = player.position + forward * 24
                missiles.append(Missile(missile_start, forward))

        if event.type == pygame.MOUSEBUTTONDOWN and not game_over:
            target = pygame.Vector2(event.pos)
            direction = target - player.position
            if direction.length() > 0:
                direction = direction.normalize()
                missile_start = player.position + direction * 24
                missiles.append(Missile(missile_start, direction))

    if not game_over:
        player.update()

        for asteroid in asteroids:
            asteroid.update()

        resolve_asteroid_collisions(asteroids)

        for enemy in enemies:
            enemy.update_fov(player)
            if enemy.sees_player:
                enemy.attack(player)
            enemy.update()

        for missile in missiles:
            missile.update()

        missiles = [missile for missile in missiles if not missile.is_off_screen()]

        for missile in missiles[:]:
            for asteroid in asteroids[:]:
                if missile_hits(missile, asteroid):
                    if missile in missiles:
                        missiles.remove(missile)
                    if asteroid in asteroids:
                        asteroids.remove(asteroid)
                        asteroids.extend(split_asteroid(asteroid))
                    score += 1
                    break

        for missile in missiles[:]:
            for enemy in enemies[:]:
                if missile_hits(missile, enemy):
                    if missile in missiles:
                        missiles.remove(missile)
                    if enemy in enemies:
                        enemies.remove(enemy)
                        enemies.append(EnemyShip())
                    score += 5
                    break

        if not asteroids:
            asteroids = [Asteroid() for _ in range(num_asteroids)]

        if player_is_hit(player, asteroids, enemies):
            player.hit()
            if player.lives <= 0:
                game_over = True

    screen.fill((10, 10, 20))

    for asteroid in asteroids:
        asteroid.draw()

    for enemy in enemies:
        enemy.draw_fov()
    for enemy in enemies:
        enemy.draw()

    for missile in missiles:
        missile.draw()

    player.draw_forward_vector()
    player.draw_velocity_vector()
    player.draw()

    spotted = sum(1 for enemy in enemies if enemy.sees_player)

    status_text = font.render(
        f"score: {score}   # of lives: {player.lives}   spotted by: {spotted}", True, (255, 255, 255)
    )
    screen.blit(status_text, (20, 15))

    controls_text = font.render("arrows: rotate/thrust   space/click: fire", True, (255, 255, 255))
    screen.blit(controls_text, (20, 40))

    velocity_text = font.render(f"velocity: ({player.velocity.x:.2f}, {player.velocity.y:.2f})", True, (80, 180, 255))
    screen.blit(velocity_text, (20, 65))

    speed_text = font.render(f"speed: {player.velocity.length():.2f}", True, (255, 255, 255))
    screen.blit(speed_text, (20, 90))

    acceleration_text = font.render(f"acceleration: ({player.acceleration.x:.2f}, {player.acceleration.y:.2f})", True, (255, 255, 255))
    screen.blit(acceleration_text, (20, 115))

    if game_over:
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        over_text = big_font.render("game over...", True, (255, 80, 80))
        score_text = font.render(f"final score: {score}", True, (255, 255, 255))
        restart_text = font.render("press R to restart :(", True, (255, 255, 255))

        screen.blit(over_text, over_text.get_rect(center=(width / 2, height / 2 - 40)))
        screen.blit(score_text, score_text.get_rect(center=(width / 2, height / 2 + 15)))
        screen.blit(restart_text, restart_text.get_rect(center=(width / 2, height / 2 + 45)))
    pygame.display.flip()
pygame.quit()