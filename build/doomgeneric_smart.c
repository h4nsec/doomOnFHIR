// doomgeneric platform layer for SmartDoom (SMART on FHIR questionnaire item).
// No SDL: frames are blitted to a <canvas> via JS, keys arrive from JS,
// and level stats are pushed to JS so they can become QuestionnaireResponse answers.

#include "doomgeneric.h"
#include "doomkeys.h"
#include "doomstat.h"
#include "d_player.h"

#include <emscripten.h>
#include <stdint.h>

#define KEYQUEUE_SIZE 64
static unsigned short keyq[KEYQUEUE_SIZE];
static unsigned int kw = 0, kr = 0;

EMSCRIPTEN_KEEPALIVE void smartdoom_key(int pressed, int doomKey)
{
    keyq[kw] = (unsigned short)(((pressed ? 1 : 0) << 8) | (doomKey & 0xFF));
    kw = (kw + 1) % KEYQUEUE_SIZE;
}

// [episode, map, kills, totalkills, items, totalitems, secrets, totalsecrets, leveltime, health, gamestate]
static int stats[11];
EMSCRIPTEN_KEEPALIVE int *smartdoom_stats(void)
{
    player_t *p = &players[consoleplayer];
    stats[0] = gameepisode;  stats[1] = gamemap;
    stats[2] = p->killcount; stats[3] = totalkills;
    stats[4] = p->itemcount; stats[5] = totalitems;
    stats[6] = p->secretcount; stats[7] = totalsecret;
    stats[8] = leveltime;    stats[9] = p->health;
    stats[10] = gamestate;
    return stats;
}

static int last_gamestate = -1;

void DG_Init(void)
{
    EM_ASM({ if (Module.onInit) Module.onInit($0, $1); }, DOOMGENERIC_RESX, DOOMGENERIC_RESY);
}

void DG_DrawFrame(void)
{
    EM_ASM({ Module.blit($0, $1, $2); }, DG_ScreenBuffer, DOOMGENERIC_RESX, DOOMGENERIC_RESY);

    if ((int)gamestate != last_gamestate)
    {
        last_gamestate = gamestate;
        // GS_INTERMISSION == 1: a level was just completed
        EM_ASM({ if (Module.onGameState) Module.onGameState($0); }, (int)gamestate);
    }
}

void DG_SleepMs(uint32_t ms) { (void)ms; } // the game loop polls the clock; never block the browser

uint32_t DG_GetTicksMs(void) { return (uint32_t)emscripten_get_now(); }

int DG_GetKey(int *pressed, unsigned char *doomKey)
{
    if (kr == kw) return 0;
    unsigned short d = keyq[kr];
    kr = (kr + 1) % KEYQUEUE_SIZE;
    *pressed = d >> 8;
    *doomKey = d & 0xFF;
    return 1;
}

void DG_SetWindowTitle(const char *title) { (void)title; }

int main(int argc, char **argv)
{
    doomgeneric_Create(argc, argv);
    emscripten_set_main_loop(doomgeneric_Tick, 0, 1);
    return 0;
}
