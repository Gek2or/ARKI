# ARKI — Nordic 2.0 Result Hub

ARKI is a Nordic weekly-planning product concept for households. It connects meals, shopping baskets, store promotions, package sizes and the real cost of a trip in one calm flow.

The enemy is not a lack of recipes. It is the 18:20 “what do we eat?” moment, followed by five tabs, three half-filled baskets and no clear total.

## The idea

Guided onboarding turns household preferences and constraints into a practical week. The **Result Hub** brings suggested meals, a shoppable basket and the **Real Cost** of selected stores into one screen.

Change one dish and ARKI recalculates the dependent products, package quantities, demo promotions, baskets and travel cost. The point is not to make another recipe catalogue. The point is to reduce decision fatigue and make the next action obvious.

## What I am building

- a multilingual, responsive Nordic client;
- a guided onboarding flow that captures real household constraints;
- a result view that connects meals to products, packages, stores and travel;
- explicit recalculation rules so a change in one part does not leave stale totals elsewhere;
- a product foundation that could later connect to real retailer data and family accounts.

## Why this project matters

ARKI comes from a customer-side question: why should a person compare meals, shopping lists, promotions, package sizes and travel cost separately when they are making one decision — “can we feed the household this week, and what will it really cost?”

That question is also the technical challenge. The useful work is in the connections between screens and data, not in adding another glossy card to a dashboard.

## Current repository status

This repository is an import-ready result hub and verification workspace for ARKI 2.0. The full application source is staged for a verified import through GitHub Actions; this repository does not claim to be a production deployment.

## Verification evidence

The existing project was checked in separate suites:

- backend and existing project: 228 checks;
- client core: 66/66;
- build and local HTTP: 9/9;
- browser regression: 109/109;
- Nordic responsive and language coverage: 140/140;
- guided onboarding and Result Hub: 40/40.

That is **592 checks** across the recorded suites.

## Honest boundaries

Live prices and feeds from K-ryhmä, S-ryhmä and Lidl are not connected. Prices and promotions are demonstrations. A possible K-ryhmä pilot is a goal, not a partnership. The Nordic client currently uses browser-local state; the closed Node/SQLite pilot is synthetic-only and has no automatic family synchronisation.

## Import workflow

1. Add the verified **ARKI_Project_v2.0_git.bundle** to the root of **main**.
2. The **Import ARKI project** workflow checks the expected SHA-256 snapshot.
3. It runs the tests, imports the source tree and removes the bundle from the working tree.

Expected snapshot:

SHA-256: d4fbef1223c2bfe91a9d3809ce9977ec04b10d0a097e3725b94ff13c1110df90
Source commit: c57919e8181ee27698e16f8c4427b35904b06b8a
Source files: 195

## What this shows a team

ARKI is a product-thinking exercise as much as a UI project: start from a frustrating customer decision, model the dependencies behind it, make the flow understandable, and keep the limitations visible.
