# Suspension Tracker

Minimal Anki add-on that records the date a card is suspended or unsuspended and makes those dates searchable.

### Overview
Every time a card is suspended or unsuspended, the add-on writes a tag to the note (`suspension-tracker::suspended::YYYY-MM-DD`, `suspension-tracker::unsuspended::YYYY-MM-DD`) <br>
These tags are overwritten with the most recent event date. The add-on also provides "Suspended" and "Unsuspended" browser columns which can be enabled by right-clicking the browser's column header.

### Searching
Search using standard tag syntax ~~or custom range token~~:

**Standard Search** <br>
`tag:suspension-tracker::unsuspended::2026-03-31` <br>
`tag:suspension-tracker::unsuspended::2026-03*`

~~**Range Search**~~ (not done) <br>
~~`tracker:unsuspended:2026-03-01:2026-04-15` <br>
`tracker:suspended:2026-03-01:*`~~

~~**UI Search**~~ (Planned) <br>
~~A dedicated "Search by Date" menu to visually select date ranges without typing tokens.~~  

### Usage Notes
Tags are stored on the **note**. If a note has multiple cards, the tag reflects the date of the most recently modified card. </br>
Only events occurring after installation are recorded; **no retroactive tracking**. <br>
The add-on tracks the **most recent** suspension or unsuspension; it does not maintain a history of previous dates.

> [!NOTE] 
> This addon was developed for users in a *unique* spot who unsuspend (e.g., during class, following along lecture, tracking high yield concepts based on cards) but do not review cards, and subsequently would like to study unsuspended cards between a certain time period (i.e., study all cards unsuspended from last exam). This is especially relevant for medical students using large, premade decks like AnKing.

### Disclaimer
This add-on is provided "as is" without warranty of any kind. While it is designed to safely interact with the Anki database using official APIs, the author is not responsible for any data loss or corruption. Users are encouraged to maintain regular backups of their Anki collection.

### License
Distributed under the GNU AGPLv3 License.
