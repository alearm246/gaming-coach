"""
One-time script to seed the meta_knowledge table with Clash Royale archetypes,
card counters, and strategic tips.

Run from the project root:
    python scripts/seed_meta.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app
from app import db
from app.models.meta_knowledge import MetaKnowledge
from app.services.embeddings import embed_text

ENTRIES = [
    # ── Archetypes ────────────────────────────────────────────────────────────
    {
        'title': 'Hog Rider Cycle Deck',
        'category': 'archetype',
        'content': (
            'Hog Rider Cycle is a fast, low-elixir deck (avg 2.8–3.4 elixir) built around cycling '
            'quickly back to the Hog Rider. Core cards: Hog Rider, Ice Spirit, Skeletons or Goblins, '
            'Cannon or Tesla, Fireball or Rocket, Musketeer or Ice Golem. Strategy: chip damage every '
            'cycle, punish opponent when they play a high-cost card. Weakness: high-HP tanks at bridge '
            'can soak Hog hits; struggles against defensive buildings like Inferno Tower. '
            'Best counters: Cannon placed defensively, Inferno Tower, Skeleton Army behind tank.'
        ),
    },
    {
        'title': 'Goblin Giant Beatdown',
        'category': 'archetype',
        'content': (
            'Goblin Giant beatdown uses the Goblin Giant (6 elixir) as a tank with Sparky or Electro '
            'Dragon on its back as a rider. High average elixir (4.0+). Push strategy: build a massive '
            'push on one lane, force the opponent to spend all elixir defending. Typical support cards: '
            'Goblin Giant, Sparky or Electro Dragon, Minions or Minion Horde, Mega Minion, Zap or '
            'Electro Spirit, Goblin Cage or Tesla, Mirror. Weakness: slow cycle means punishes are rare; '
            'vulnerable to split-lane pressure. Counter: Inferno Tower melts Goblin Giant; Electro '
            'Wizard resets Sparky; swarm units kill support.'
        ),
    },
    {
        'title': 'Golem Beatdown',
        'category': 'archetype',
        'content': (
            'Golem beatdown is the classic high-elixir (4.5+) push deck. Golem (8 elixir) soaks all '
            'damage while Night Witch, Baby Dragon, or Lumberjack deal damage behind it. Play Golem only '
            'in double-elixir or when you have +2 elixir advantage. Strengths: once a full push forms '
            'it is almost unstoppable. Weaknesses: extremely slow to build; any counter-push during your '
            'build-up can be lethal. Best counters: Inferno Tower, Inferno Dragon (locks on), split-lane '
            'pressure while Golem is building.'
        ),
    },
    {
        'title': 'X-Bow Siege',
        'category': 'archetype',
        'content': (
            'X-Bow siege places the X-Bow (6 elixir) at the bridge to deal massive long-range damage '
            'to towers. Paired with Tesla or Cannon for defence, Ice Golem or Ice Spirit to tank for '
            'the X-Bow, and Archers or Skeletons for distraction. Avg elixir: 3.0–3.5. Strategy: never '
            'over-commit; defend efficiently and cycle to X-Bow. The deck wins by out-chipping and '
            'out-cycling opponents. Weakness: balloon or fast air units bypass defences; lava hound '
            'decks can be difficult. Counter: Mega Knight or Pekka placed on X-Bow, high-cost spells '
            'like Rocket or Lightning.'
        ),
    },
    {
        'title': 'Mortar Siege',
        'category': 'archetype',
        'content': (
            'Mortar siege is similar to X-Bow siege but uses the cheaper Mortar (4 elixir) allowing '
            'more frequent placement and faster cycling (avg elixir 2.8–3.2). The Mortar pushes damage '
            'from a distance and can target the king tower. Core: Mortar, Tesla, Ice Spirit, Skeletons, '
            'Archers or Musketeer, Fireball, Log. Weakness: more fragile than X-Bow because Mortar is '
            'cheaper to counter. Play style: never panic, always defend first then place Mortar on '
            'counter-push.'
        ),
    },
    {
        'title': 'Graveyard Control',
        'category': 'archetype',
        'content': (
            'Graveyard control uses the Graveyard spell (5 elixir) to spawn skeletons directly on the '
            'opponent\'s tower, paired with a tank (Ice Golem, Knight, or Giant) to distract defences. '
            'Support: Poison behind Graveyard for maximum skeleton survival, Minions or Mega Minion '
            'for air defence, Tombstone for counter-defence, Archers or Electro Wizard. Avg elixir: '
            '3.4–3.9. Strategy: get Graveyard + Poison off with a tank in front. One good push often '
            'ends the game. Weakness: Skeleton Army or Valkyrie counters the skeletons cheaply; Tornado '
            'can pull them off the tower. Counter: Splash damage (Valkyrie, Wizard, Baby Dragon) inside '
            'the Graveyard zone.'
        ),
    },
    {
        'title': 'Lava Hound LavaLoon',
        'category': 'archetype',
        'content': (
            'LavaLoon is a sky-high beatdown deck centred on Lava Hound (7 elixir) + Balloon (5 elixir). '
            'The Lava Hound tanks all air-targeting defences while the Balloon deals huge tower damage. '
            'Support: Minions, Minion Horde, Mega Minion, Tombstone, Arrows or Zap, Lightning. Avg '
            'elixir: 4.2–4.7. Strategy: get Lava Hound in the back, stack Balloon on top of it, '
            'Lightning key defences. Weakness: fast cycle decks punish the slow build; Inferno Tower '
            'melts the Hound before Balloon arrives. Counter: Inferno Tower or Inferno Dragon, Tesla, '
            'Electro Dragon resets Balloon freeze.'
        ),
    },
    {
        'title': 'Balloon Freeze Cycle',
        'category': 'archetype',
        'content': (
            'Balloon Freeze pairs the Balloon (5 elixir) with Freeze (4 elixir) for guaranteed tower '
            'damage. Typically run with Hog Rider or Miner to pressure the tower and Electro Spirit '
            'or Ice Spirit for cheap cycling. Avg elixir: 3.5–3.8. Strategy: wait for double-elixir, '
            'punish exposed towers, cycle Freeze quickly. Weakness: Inferno Tower still fires through '
            'Freeze reset delay; air swarms are expensive to deal with. Counter: Inferno Tower + any '
            'splash (Baby Dragon), high-HP air unit to trade with Balloon.'
        ),
    },
    {
        'title': 'Bridge Spam',
        'category': 'archetype',
        'content': (
            'Bridge spam decks deploy multiple high-value units at the bridge in rapid succession to '
            'overwhelm defences. Key cards: Battle Ram, Ram Rider, Bandit, Magic Archer, Dark Prince, '
            'Electro Spirit, Fireball. Avg elixir: 3.3–3.8. Strategy: pressure from both lanes; never '
            'let the opponent stabilise. Every big defense they make, counter-push immediately. '
            'Weakness: defensive tanks like Pekka or Mega Knight can shut down single-bridge-spam units '
            'cheaply. Counter: Pekka + Mini Pekka behind bridge; buildings like Bomb Tower to redirect.'
        ),
    },
    {
        'title': 'Three Musketeers Split Push',
        'category': 'archetype',
        'content': (
            'Three Musketeers (9 elixir) are split into both lanes simultaneously, forcing the opponent '
            'to defend two threats at once. Support: Battle Ram or Goblin Barrel as secondary threat, '
            'Elixir Collector for pumping ahead, Lightning or Poison for support. Avg elixir: 4.0–4.5. '
            'Strategy: pump elixir early; split Three Musketeers when opponent has just spent elixir. '
            'Weakness: Lightning or Rocket kills all three if not split in time. Counter: Lightning the '
            'cluster, then counter-push immediately on the bank.'
        ),
    },

    # ── Card Counters ─────────────────────────────────────────────────────────
    {
        'title': 'How to counter Giant',
        'category': 'card_counter',
        'content': (
            'Giant (5 elixir) is a tank that only targets buildings. Counters: Inferno Tower (melts it '
            'fast for 4 elixir, great positive trade), Skeleton Army (positive elixir trade if no spell), '
            'Cannon + Musketeer to kill support behind Giant, Tombstone to distract Giant while you kill '
            'support. Never use Mini Pekka alone — it takes too much damage. Tornado + Executioner is '
            'very efficient against Giant pushes.'
        ),
    },
    {
        'title': 'How to counter Hog Rider',
        'category': 'card_counter',
        'content': (
            'Hog Rider (4 elixir) targets only buildings. Counters: Cannon (3 elixir, outstanding '
            'positive trade), Tesla (placed on tower side to intercept), Mini Pekka (kills Hog and '
            'provides counter-push), Goblin Cage (Brawler re-engages if Hog is reset). Never use '
            'Skeleton Army alone — it dies to supporting Fireball or Zap. Inferno Tower is overkill '
            'but works. The key is placing the building centrally so the Hog is forced to target it.'
        ),
    },
    {
        'title': 'How to counter Balloon',
        'category': 'card_counter',
        'content': (
            'Balloon (5 elixir) targets only buildings and deals massive bomb damage on death. Counters: '
            'Inferno Tower (locks on and melts it before it reaches the tower), Inferno Dragon, Minion '
            'Horde (kill it fast but expensive if paired with Freeze), Tesla. The death bomb is dangerous '
            '— always try to kill the Balloon over the river, not over your tower. Electro Dragon and '
            'Mega Minion are solid air-targeting units to keep cycling.'
        ),
    },
    {
        'title': 'How to counter Sparky',
        'category': 'card_counter',
        'content': (
            'Sparky resets on stun. Counters: any electric card (Electro Wizard, Electro Spirit, Zap) '
            'resets its charge — Electro Wizard is ideal as it also deals damage and prevents re-charge. '
            'Swarm units like Skeleton Army or Minion Horde force Sparky to discharge on chaff before '
            'reaching the tower. Inferno Dragon also resets from opponent\'s own Zap. Never let Sparky '
            'charge freely against your push — always have a reset or swarm ready.'
        ),
    },
    {
        'title': 'How to counter Mega Knight',
        'category': 'card_counter',
        'content': (
            'Mega Knight (7 elixir) deals jump damage on placement. Counters: Pekka (out-damages MK in '
            'a 1v1 while being cheaper to support), Inferno Dragon (locks on and melts), Skeleton Army '
            'at a distance so it doesn\'t get hit by jump, Mini Pekka for chip trading. Never place '
            'swarms right next to where MK will land. Use Tornado to move MK away from your tower. '
            'Goblin Barrel is a classic counter-push after MK is placed.'
        ),
    },
    {
        'title': 'How to counter Goblin Barrel',
        'category': 'card_counter',
        'content': (
            'Goblin Barrel (3 elixir) spawns three Goblins on the tower. Counters: Log (best — same '
            'elixir cost, full counter), Zap (works but leaves one Goblin alive), Princess (pre-placed '
            'on tower), Arrows (kills all goblins), Tornado to pull away from tower. Timing: wait for '
            'the Barrel to travel before throwing your spell — placing it too early lets opponent adjust '
            'the throw angle. If you have no Log or Zap, Skeleton Army or Goblin Gang can trade.'
        ),
    },
    {
        'title': 'How to counter Graveyard',
        'category': 'card_counter',
        'content': (
            'Graveyard spawns skeletons over 9 seconds. Counters: any splash that stays inside the '
            'Graveyard zone — Valkyrie, Wizard, Baby Dragon, Tornado into a splash unit. Poison placed '
            'inside the Graveyard zone kills skeletons as they spawn. Electro Wizard also works '
            'passively. The tank in front must be killed quickly with a single-target unit. '
            'Never let a Graveyard + Poison combo land without a response.'
        ),
    },
    {
        'title': 'How to counter Lava Hound',
        'category': 'card_counter',
        'content': (
            'Lava Hound (7 elixir) has massive HP but low DPS; its Lava Pups on death are the real '
            'threat. Counters: Inferno Tower locks on and melts the Hound before Balloon arrives; '
            'Inferno Dragon is air-locking and threatens the Hound. Kill the Lava Hound over the '
            'river to push Pups away from your tower. Electro Dragon resets Inferno targeting so '
            'be careful. Minion Horde after Pups spawn for a positive elixir trade.'
        ),
    },
    {
        'title': 'How to counter Pekka',
        'category': 'card_counter',
        'content': (
            'Pekka (7 elixir) is slow and only targets ground. Counters: Inferno Tower (most elixir-'
            'efficient), Tombstone (distracts Pekka while skeletons chip), Mini Pekka behind a tank '
            'for a counter-push, Balloon or Minions to fly over. Tornado + Executioner handles Pekka '
            'plus any support. Avoid Skeleton Army alone — the opponent likely has Zap. Minion Horde '
            'is good but costs the same elixir. The best play is defend with minimal elixir and '
            'immediately counter-push on the other lane.'
        ),
    },
    {
        'title': 'How to counter Miner',
        'category': 'card_counter',
        'content': (
            'Miner (3 elixir) digs directly to a target — usually the tower or a building. The key is '
            'predicting the landing spot. A Tesla or Cannon placed centrally can intercept Miner before '
            'it reaches the tower. Skeleton Army placed on the Miner landing spot kills it fast (positive '
            'trade). Goblin Gang or Guards also work. Buildings force the Miner to target them instead '
            'of the tower. If the opponent uses Miner + Poison together, the Poison is more dangerous '
            '— prioritise removing the Poison source.'
        ),
    },

    # ── Tips ──────────────────────────────────────────────────────────────────
    {
        'title': 'Elixir advantage and when to push',
        'category': 'tip',
        'content': (
            'Never start a big push when you are at even or negative elixir. Only commit heavy pushes '
            'when you have +2 elixir advantage or after a successful defense. If you just spent 5 elixir '
            'defending and the opponent spent 8, you have +3 advantage — that is the moment to counter-push '
            'before they can recover. Elixir leaked (unused elixir when at 10) is always bad; it means you '
            'are waiting too long to play cards.'
        ),
    },
    {
        'title': 'Elixir leak reduction',
        'category': 'tip',
        'content': (
            'Elixir leaks when your elixir bar is at 10 and you are not spending it. Every 2.8 seconds '
            'of capped elixir is wasted elixir. Solutions: cycle a cheap card (Ice Spirit, Skeletons) '
            'defensively, start building a push in the back, place an elixir collector. High elixir leak '
            'usually signals a player being passive or unsure what to play — practice fast decision-making '
            'to reduce hesitation.'
        ),
    },
    {
        'title': 'Tower targeting and lane selection',
        'category': 'tip',
        'content': (
            'Always push on the lane where the opponent\'s princess tower is already damaged. Splitting '
            'damage between two towers is much weaker than focusing one. Once a princess tower is destroyed, '
            'all your troops target the king tower automatically — that is where you win. In overtime, '
            'the team with more tower damage wins, so switching to a secondary tower attack only makes '
            'sense if the primary tower has <100 HP remaining.'
        ),
    },
    {
        'title': 'When to use spells offensively vs. defensively',
        'category': 'tip',
        'content': (
            'Spells like Fireball (4 elixir) and Rocket (6 elixir) deal tower damage and should be used '
            'offensively when they can hit both a unit and the tower simultaneously — otherwise you are '
            'over-paying. Never Rocket a single unit away from the tower; it is a negative elixir trade. '
            'Log (2 elixir) and Zap (2 elixir) are cycle spells — use them to reset or clear chaff '
            'defensively. Poison (4 elixir) is best inside a Graveyard or at the tower with slow units '
            'present, because its 8-second duration amplifies the damage.'
        ),
    },
    {
        'title': 'Double elixir strategy',
        'category': 'tip',
        'content': (
            'Double elixir (starts at 2:00) means the game speeds up dramatically. Beatdown and high-'
            'elixir decks benefit most — this is when to make your biggest pushes with Golem or Three '
            'Musketeers. Cycle decks need to spam pressure on both lanes simultaneously. If you are '
            'behind on tower damage, double-elixir is your window to equalise — never play defensively '
            'if you are losing. Always have an answer to a big push ready before committing a double-'
            'elixir offense.'
        ),
    },
    {
        'title': 'Reading the opponent\'s deck',
        'category': 'tip',
        'content': (
            'Track every card the opponent plays and note what they have not played yet. After 4–5 cards '
            'are revealed, you can infer the remaining cards and anticipate their counter to your next push. '
            'If you see a Golem, expect Night Witch and Lightning in their deck. If you see Graveyard, '
            'save your splash unit for when it is played. Knowing their full deck lets you push when '
            'their key defensive card is in the back half of rotation (just played).'
        ),
    },
    {
        'title': 'King tower activation',
        'category': 'tip',
        'content': (
            'Activating your own king tower early is often a correct play. The king tower has 2400 HP and '
            'deals meaningful damage. Any push that crosses the bridge on the side opposite your active '
            'princess tower can be funnelled into the king tower range with a Tornado. Once activated, '
            'the king tower fires for the rest of the game — it is a significant defensive advantage. '
            'Some decks (Graveyard control) intentionally activate their king tower via Tornado.'
        ),
    },
    {
        'title': 'Chip damage strategy',
        'category': 'tip',
        'content': (
            'Chip damage accumulates over the 3-minute game and can be decisive in overtime. Cheap units '
            'like Goblin Barrel (3 elixir), Miner (3 elixir), or Skeletons at the bridge deal small but '
            'consistent tower hits. Against a strong defensive deck, chip is sometimes the only reliable '
            'win condition. Track cumulative damage — 100 chip hits per cycle over 10 cycles is 1000 '
            'damage, often enough to get a tower kill. Fireball cycling on the tower is a common chip tactic.'
        ),
    },

    # ── Card Info ─────────────────────────────────────────────────────────────
    {
        'title': 'Tornado — offensive and defensive uses',
        'category': 'card_info',
        'content': (
            'Tornado (3 elixir) pulls all units toward a target point for 2 seconds. Offensive uses: '
            'pull enemy troops off your push path or into a Executioner/Bowler\'s attack. Defensive uses: '
            'activate your king tower by pulling troops into its range (king tower activates permanently '
            'once it fires). Tornado + Executioner is one of the most powerful defensive combinations '
            'in the game, handling nearly any push. Tornado also pulls flying units, making it useful '
            'against LavaLoon pushes.'
        ),
    },
    {
        'title': 'Electro Wizard — why it is so versatile',
        'category': 'card_info',
        'content': (
            'Electro Wizard (4 elixir) has a passive zap on deployment (resets Inferno Tower/Dragon, '
            'Sparky, Goblin Cage Brawler) and fires chain lightning hitting two targets simultaneously. '
            'This makes it the best single-card answer to Sparky. It also prevents Skeleton Army from '
            'overwhelming it by chaining between skeletons. On offense, it stalls air swarms. '
            'Weakness: fairly fragile — Fireball or Poison will delete it quickly.'
        ),
    },
    {
        'title': 'Inferno Tower vs Inferno Dragon',
        'category': 'card_info',
        'content': (
            'Inferno Tower (5 elixir) is a stationary building that locks onto the highest-HP target '
            'in range and ramps up damage over time — best against slow single-target pushes (Golem, '
            'Giant, Pekka). Inferno Dragon (4 elixir) is a flying unit that provides both offensive and '
            'defensive value — it can fly over walls, follow targets, and threatens towers. Both are '
            'reset by any stun (Zap, Lightning, Electro Wizard deployment). The Tower is more defensively '
            'reliable; the Dragon is more flexible but easier to kite.'
        ),
    },
    {
        'title': 'Poison vs Fireball — when to choose each',
        'category': 'card_info',
        'content': (
            'Fireball (4 elixir): instant damage in an area, great for killing support troops quickly '
            'or dealing chip to the tower alongside a push. Use when you need immediate damage. '
            'Poison (4 elixir): deals damage over 8 seconds in a persistent zone, much higher total '
            'damage if units stay inside. Best against swarms, paired with Graveyard, or cycling '
            'against the tower with a tank in front. Rule of thumb: Fireball kills faster, Poison '
            'kills more total. Never use Poison purely as a reactive defensive spell — the damage '
            'is wasted if units leave the zone quickly.'
        ),
    },
    {
        'title': 'Skeleton Army — best and worst uses',
        'category': 'card_info',
        'content': (
            'Skeleton Army (3 elixir, 16 skeletons) is the most elixir-efficient counter to single '
            'high-HP units: Pekka, Golem, Giant, Mega Knight (if placed at a distance from the jump). '
            'Positive elixir trades against 5-8 elixir units are common. Worst uses: against any splash '
            'damage (Baby Dragon, Valkyrie, Wizard) — a single Zap kills the entire army for 2 elixir, '
            'a massive negative trade. Always predict whether the opponent has a response before playing '
            'Skeleton Army defensively.'
        ),
    },
]


def run():
    app = create_app()
    with app.app_context():
        existing = MetaKnowledge.query.count()
        if existing > 0:
            print(f'Meta knowledge table already has {existing} entries. Skipping seed.')
            print('To re-seed, delete existing rows first: DELETE FROM meta_knowledge;')
            return

        print(f'Seeding {len(ENTRIES)} meta knowledge entries...')
        for i, entry in enumerate(ENTRIES):
            embedding = embed_text(entry['content'])
            if embedding is None:
                print(f'  Warning: failed to embed "{entry["title"]}", skipping')
                continue
            row = MetaKnowledge(
                title=entry['title'],
                category=entry['category'],
                content=entry['content'],
                embedding=embedding,
            )
            db.session.add(row)
            if (i + 1) % 10 == 0:
                print(f'  {i + 1}/{len(ENTRIES)} embedded...')

        db.session.commit()
        print(f'Done. {MetaKnowledge.query.count()} entries in meta_knowledge table.')


if __name__ == '__main__':
    run()
