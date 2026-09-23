# indie-marketing-skills

Claude Code skills for indie hackers who do their own growth. Built while
growing a real consumer app solo, then stripped of everything specific to it.

## posthog-growth

Five skills that turn Claude into the analyst you don't have, on top of the
[PostHog MCP server](https://posthog.com/docs/model-context-protocol).

| Skill | Ask Claude… | What it does |
|---|---|---|
| `posthog-funnel-map` | "set me up", "map my funnel" (runs automatically the first time) | Short interview about your business (model, price, traffic, what "converted" means), then reads your dashboards, saved insights, actions, goals, events, flags, replay and heatmap settings, finds the noise (bots with PostHog's own classifier, App Store reviewers, you) and writes `.claude/posthog-funnel-map.md`. The other skills never guess an event name again. |
| `posthog-investigation` | "why zero sales this week?", "analyze my sessions", "did the deploy break onboarding?" | Reconstructs what changed (commits, deploys, flags, annotations, campaigns), rules out false alarms, walks a list of causes including mix-shift, finds who dropped and where they went, reads replays and heatmaps of the sessions that matter, cross-checks on a control segment. Ends with one bottleneck, a confidence level, causes ruled out and prioritized fixes. |
| `posthog-paid-funnel` | "is my TikTok campaign converting?", "should I kill the Google Ads?" | Follows paid visitors by UTM from landing to payment, checks tagging and blind spots (store CTAs, external checkout), judges quality vs volume with sourced benchmarks and margins of error, computes cost per signup and per customer, reads replays and heatmaps of paid visitors who dropped. |
| `posthog-experiment-reader` | "can I call my A/B test?", "did the new paywall win?" | Checks the setup (split, sample ratio mismatch, people in both arms), computes lift with its margin, flags peeking, short runs and mix-shift, estimates when the test becomes readable at your traffic, reads replays per variant, returns a verdict. |
| `posthog-weekly-brief` | "give me a weekly growth brief", "keep an eye on my funnel" | Keeps a watchlist of up to 8 flows with baselines in a file, reports only what moved beyond normal, attributes it, lists running experiments, and hands off to the investigation when something looks bad. Schedulable. |

### Lessons baked in

- Ad platforms' "conversions" are usually landing-page clicks. On one
  campaign: 104 visitors, 39 CTA clicks, 5 signups, 0 customers, while the
  platform reported dozens of conversions.
- On mobile, most paid traffic leaves for the App Store and comes back
  untagged: the web funnel may cover only 15 % of your spend. Say it.
- PostHog's own scanners, Apple's App Review and your own test accounts can
  be the only "purchase attempts" of the day. Filter them.
- A before/after around a deploy found what the daily funnel hid: paywall CTA
  clicks falling from 27 % to 9 % after a "small" UI change.

## Install

In Claude Code:

```
/plugin marketplace add josephbedminster/indie-marketing-skills
/plugin install posthog-growth@indie-marketing-skills
```

Then connect the PostHog MCP server (`https://mcp.posthog.com/mcp`, OAuth).
For replay summaries, grant the `replay_scanner:read` and
`replay_scanner:write` scopes; for conversion goals, `marketing_analytics:read`.
Without them the skills still work and tell you what they couldn't see.

Everything these skills do in PostHog is read-only, except creating an annotation, a replay scanner or a saved replay filter, which they only do after asking you.

Works best next to PostHog's official plugin (`claude plugin install
posthog`): these skills bring the method and the founder context, the
official ones cover every PostHog product in depth.

## Credits

Built on ideas from, and partly adapted from (all MIT):

- [PostHog/ai-plugin](https://github.com/PostHog/ai-plugin): replay
  shortlisting and investigation, metric investigation playbooks, bot
  traffic classification, heatmap reading, experiment diagnostics.
- [clamp-sh/analytics-skills](https://github.com/clamp-sh/analytics-skills):
  the business profile, the channel quality matrix, benchmarks, experiment
  reading discipline.

## License

MIT
