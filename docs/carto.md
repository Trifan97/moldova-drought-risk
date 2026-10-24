# Building the CARTO dashboard

Click-by-click guide for loading the pipeline outputs into CARTO and building the dashboard in Builder. Written against CARTO's documentation in October 2026 and corrected while building the map in a CARTO trial. CARTO changes its interface over time: where the docs don't name a button, this guide says what to look for.

**Live map built with this guide:** [Moldova drought-risk change (SYNTHETIC DATA, demo)](https://pinea.app.carto.com/map/e9fbaa6e-0855-4e3d-bd75-610b5b8bb5aa)

**What you'll build:** one map with two layers and three widgets.

| Layer | Source table | Shows |
|---|---|---|
| Change in drought frequency | `synthetic_district_drought_risk` (37 polygons) | Main map: change in the share of drought months, 1961–1990 → 1991–2020 |
| Monthly severity | `synthetic_district_monthly_spei` (26,640 points) | One point per district per month, coloured by severity, filtered by the time-series chart |

## 0. Before you start

1. Run the pipeline so the two files exist:

   ```powershell
   python -m moldova_drought
   ```

2. Find them in `data\processed\`:
   - `synthetic_district_drought_risk.parquet`
   - `synthetic_district_monthly_spei.parquet`
3. Sign in to your CARTO workspace. It comes with a connection called **CARTO Data Warehouse**; the tables go there.

## 1. Import the two tables

1. In the workspace's left menu, open **Data Explorer**.
2. Click **Import data** (top right). Choose **Local file**, select `synthetic_district_drought_risk.parquet` and click **Continue**.
3. Destination:
   - Connection: **CARTO Data Warehouse**.
   - Location: a folder you can write to. If a folder shows a permissions warning, pick another one.
   - Table name: `synthetic_district_drought_risk`.
4. Leave **Let CARTO automatically define the schema** switched on and click **Import**.
5. Repeat for `synthetic_district_monthly_spei.parquet`, table name `synthetic_district_monthly_spei`.
6. Check both tables in Data Explorer's preview before going on:

   | Table | Rows | Check |
   |---|---|---|
   | `synthetic_district_drought_risk` | 37 | Has a geometry column; `drought_change_pp` is a number |
   | `synthetic_district_monthly_spei` | 26,640 | `date` is a date/timestamp type, **not text**; `severity` is text; `severity_code` is an integer |

   If `date` arrived as text, stop here: the Time Series widget needs a timestamp column.

## 2. Create the map and add both sources

1. Open **Maps** in the left menu and create a new map (on a new account the button reads **Create your first map**).
2. Click **Add source from…**, open **CARTO Data Warehouse**, find `synthetic_district_drought_risk` and add it. Builder creates a layer for it automatically.
3. Click **Add source from…** again and add `synthetic_district_monthly_spei`.
4. In the layer list, drag the monthly layer **above** the risk layer, so the points draw on top of the polygons.

## 3. Style the main layer: change in drought frequency

1. Click the layer's card to open its panel. Rename it with the three-dot menu at the top of the panel: `Change in drought frequency (synthetic)`.
2. In the **Fill** section, open the **Color** dropdown and choose **by drought_change_pp**.
3. Click the palette strip under it and pick a **diverging** palette with **6** steps, running from teal (lowest values) to red or brown (highest). In the October 2026 trial, custom hex colours weren't offered; a built-in teal-to-red palette does the job. If your workspace does offer custom colours, ColorBrewer's BrBG works well: `#01665e`, `#5ab4ac`, `#c7eae5`, `#f6e8c3`, `#d8b365`, `#8c510a`.
4. Click the sliders icon at the right of the **Fill** heading (advanced fill options). Set **Data classification method** to **Custom** and enter the breaks `-4`, `-2`, `0`, `2`, `4`:

   | Class (percentage points) | Meaning |
   |---|---|
   | below −4 | much less drought |
   | −4 to −2 | less drought |
   | −2 to 0 | slightly less drought |
   | 0 to +2 | slightly more drought |
   | +2 to +4 | more drought |
   | above +4 | much more drought |

5. Opacity (the % box next to the palette): 55–85%, so place names on the basemap stay readable.
6. **Stroke:** Simple colour, white, weight 1, so neighbouring districts stay distinguishable.

Why these choices:

- **Breaks centred on 0:** the colour family tells you the direction (red/brown = more drought, teal = less) and the shade tells you the size. On the current data the six classes hold 5, 9, 9, 4, 5 and 5 districts.
- **Not the default classification:** Builder's default splits the range from −5.9 to +5.7 into equal steps, which puts the middle break at −0.1. Criuleni and Dubasari, both at −0.1 (slightly *less* drought), would then be coloured on the "more drought" side. Quantile breaks have the same flaw: they follow the data's spread, not zero.
- **A diverging palette with red/brown for "drier"**, used on both layers, so the dashboard has one colour language.

## 4. Style the monthly layer: severity points

1. Close the open layer panel (the **×** at its top right) to get back to the layer list, then click the monthly layer's card. Rename it: `Monthly severity (synthetic)`.
2. In the **Fill** section, open the **Color** dropdown and choose **by severity**.
3. Pick a **diverging** palette with **7** steps from the same family as the main map, so red/brown means dry. Check the step count: with a 6-step palette only 6 categories get a colour, and "Extreme wet" falls into the grey "Others" group together with "No data".
4. Click the sliders icon at the right of the **Fill** heading. Set **Data classification method** to **Custom**, give each palette row a category in this order, then click **Apply**:

   | Palette row | Category |
   |---|---|
   | 1 (darkest red/brown) | Extreme drought |
   | 2 | Severe drought |
   | 3 | Moderate drought |
   | 4 (palest, middle) | Normal |
   | 5 | Moderate wet |
   | 6 | Severe wet |
   | 7 (darkest teal) | Extreme wet |

   "No data" has no row, so it is drawn in grey as "Others". That's correct: it's the 74 Jan–Feb 1961 rows.

   The Custom method keeps each colour attached to its category even when the time filter changes which categories are visible. The alternative, "Ordinal (dynamic)", gives colours to the most frequent categories first, so "Extreme drought" could turn teal.
5. Point radius about 6; stroke dark grey, weight 0.5, so pale "Normal" points stay visible on a light basemap.

Until you pick a period in the time-series chart (step 6), each dot is 720 months stacked on top of each other. That's expected: the chart is how you choose the month.

## 5. Pop-ups (Interactions)

Interactions are off by default; switch them on per layer.

**Risk layer:** turn interactions on, choose **Click** and a pop-up, then add these fields with these labels:

| Field | Label |
|---|---|
| `district` | District |
| `drought_change_pp` | Change in drought months (percentage points) |
| `drought_pct_1961_1990` | Drought months 1961–1990 (%) |
| `drought_pct_1991_2020` | Drought months 1991–2020 (%) |
| `station` | Station used |
| `station_inside` | Station inside district |
| `distance_km` | Distance to station (km) |
| `driest_month` | Driest month |
| `driest_spei_3` | Driest SPEI-3 |

Also add a **Hover** pop-up with `district` and `drought_change_pp`, so viewers see the number behind each colour; `station` and `distance_km` fit too. Hover pop-ups show at most 5 fields.

**Monthly layer:** a **Hover** pop-up with these labels:

| Field | Label | Format |
|---|---|---|
| `district` | District | |
| `date` | Date | |
| `spei_3` | SPEI-3 | 2 decimals |
| `severity` | Severity class | |

Two decimals is enough for an index like SPEI; the six stored decimals claim more precision than it has. Without a time selection, hovering a dot shows whichever of the district's 720 stacked months is on top.

## 6. Widgets

Click **New Widget**, pick the source, then the widget type.

1. **Time Series**, source `synthetic_district_monthly_spei`:
   - Date column: `date`.
   - Operation: custom aggregation, with this SQL expression:

     ```sql
     SUM(CASE WHEN severity_code <= -1 THEN 1 ELSE 0 END)
     ```

     It counts districts at Moderate drought or worse. Plain `CASE WHEN` is standard SQL, so it works in any warehouse.
   - Interval: monthly if you can set it (0–37 per month; the record peaks at 33). With a yearly interval the value becomes district-months per year.
   - Chart type: Line. Title: `Districts in drought (SPEI-3 ≤ −1)`.
   - **Split by** is optional. Without it you get one line: the total number of districts in drought. Split by `severity`, the expression gives one line per drought class (Moderate, Severe, Extreme) while the wet classes stay at 0; the published map uses this to show drought intensity. Don't combine Split by with plain COUNT: that draws 8 overlapping lines across 720 months, which is unreadable.
   - If the custom expression is rejected, use **AVG** of `spei_3` instead and title it `Average SPEI-3 across districts`. Treat it as an indicator only: an average of standardised values is not itself a standardised index.
2. **Category**, source `synthetic_district_monthly_spei`:
   - Column `severity`, operation **COUNT**.
   - Title: `Severity classes`. It follows whatever period you select in the time-series chart.
   - A Pie widget shows the same data, but its smallest and most interesting slices (Extreme drought 1.3%, Extreme wet 1.2%) are hard to tell apart; the Category widget's bars and counts read better.
   - Its totals must match the pipeline output: Normal 16,884, Moderate wet 3,292, Moderate drought 3,080, Severe drought 1,609, Severe wet 1,036, and "Others" 739 (Extreme drought 342 + Extreme wet 323 + No data 74).
3. **Histogram**, source `synthetic_district_drought_risk`:
   - Column `drought_change_pp`.
   - Title: `Districts by change in drought frequency (pp)`.

Selecting a period in the time-series chart filters only the monthly layer and its widgets. CARTO can only filter across different sources on a shared date column, and the risk table has none by design: it summarises all 60 years.

## 7. Legend

The legend shows each layer's name, so rename both layers first (step 3 and step 4). Then open the **Legend** panel from the icons down the left edge of Builder. Each layer has a card with a visibility switch, an editable label for the colour column, and an editable label for every class.

1. **Check the classes.** The risk layer should read `< -4.00`, `-4.00 – -2.00`, `-2.00 – 0.00`, `0.00 – 2.00`, `2.00 – 4.00`, `> 4.00`. A different value there means a break was mistyped in step 3; one entered as 2.4 instead of 4 makes the red side lopsided.
2. **Optional friendlier labels.** For example, set the column label to `Change in drought months, 1961–1990 → 1991–2020 (pp)` and the classes to `below −4 (much less drought)` … `above +4 (much more drought)`. For the monthly layer, `SPEI-3 severity class`.
3. **Order of the monthly classes.** Builder sorts by **Value** (most frequent first) or **Alphabetical**; neither gives Extreme drought → Extreme wet. Keep **Value**: alphabetical puts "Extreme drought" next to "Extreme wet", and the colours already carry the dry-to-wet order.

If Builder offers an option to open the legend when the map loads, switch it on.

## 8. Basemap, title and description

1. **Basemap:** a light one such as CARTO Positron, so both red and teal read clearly.
2. **Map title:** click the map's name at the top left of Builder and enter `Moldova drought-risk change (SYNTHETIC DATA, demo)`.
3. **Description:** click the **i** (Show map description) button at the top right and paste this Markdown:

   ```markdown
   **Synthetic data: not real observations.** The climate values were generated to mimic the statistics of Moldovan station records. Do not use them to judge drought conditions in Moldova: this map demonstrates the method, and on synthetic data the pattern is random.

   **Main map:** change in the share of months in drought (SPEI-3 ≤ −1.00) between the WMO climate normals 1961–1990 and 1991–2020, in percentage points. Red = drought became more frequent, teal = less frequent.

   **Points:** monthly SPEI-3 severity class for each district. Select a period in the time-series chart to filter them.

   **Method:** each district uses the station inside it, or else the nearest station (see the pop-up for the distance). SPEI after Vicente-Serrano et al. (2010); severity thresholds after McKee et al. (1993).

   **Boundaries:** geoBoundaries (Runfola et al. 2020), source UNHCR and OCHA FISS, licence CC BY 3.0 IGO.
   ```

   Once the code is on GitHub, add a final line linking to the repository.

## 9. Viewer settings and sharing

1. Open the viewer settings (the icon next to **Preview**) and switch on **Show title in public map**, so the "SYNTHETIC DATA" title is visible to everyone.
2. Leave the description open, so viewers see it first.
3. Click **Share**, choose **Public** and save.
4. Click **Publish updates**. Viewers see a published snapshot, so repeat this after every later change.
5. Click **Copy map link**.

## 10. Final check

Open the link in a private browser window, where you're not signed in, and check:

- [ ] The title says SYNTHETIC DATA and the description opens first.
- [ ] Red districts have a positive change in the pop-up, teal ones a negative change.
- [ ] Clicking a district shows its station, whether the station is inside, and the distance.
- [ ] Selecting a period in the time-series chart filters the points and the category widget. For August 1963 the tooltip shows 18 districts in drought (11 Moderate, 5 Severe, 2 Extreme), and the map should show the same 18 drought-coloured dots.
- [ ] Both legend labels read correctly.
- [ ] The boundaries credit (geoBoundaries, CC BY 3.0 IGO) is in the description.

## If a label doesn't match

CARTO renames things between releases. Look for the nearest equivalent; the steps' order and intent stay the same. Note the label you actually saw, so this guide can be updated.

## Sources

- [Importing data](https://docs.carto.com/carto-user-manual/data-explorer/importing-data)
- [Creating your first map](https://docs.carto.com/getting-started/quickstart-guides/creating-your-first-map)
- [Layers](https://docs.carto.com/carto-user-manual/maps/layers)
- [Interactions](https://docs.carto.com/carto-user-manual/maps/interactions)
- [Widgets](https://docs.carto.com/carto-user-manual/maps/widgets), [Time Series widget](https://docs.carto.com/carto-user-manual/maps/widgets/time-series-widget), [Category widget](https://docs.carto.com/carto-user-manual/maps/widgets/category-widget)
- [Legend](https://docs.carto.com/carto-user-manual/maps/legend)
- [Map description](https://docs.carto.com/carto-user-manual/maps/map-description)
- [Map settings for viewers](https://docs.carto.com/carto-user-manual/maps/publishing-and-sharing-maps/map-settings-for-viewers)
- [Sharing and collaboration](https://docs.carto.com/carto-user-manual/maps/sharing-and-collaboration)
