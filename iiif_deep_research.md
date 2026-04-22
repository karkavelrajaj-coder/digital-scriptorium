# IIIF Deep Research: International Image Interoperability Framework

The **International Image Interoperability Framework (IIIF)**, pronounced "Triple-Eye-Eff," is a set of open technical standards designed to provide a unified way to deliver high-quality, attributed digital images and other media (audio, video, 3D) over the web.

## 1. Core Purpose & Value Proposition
Before IIIF, every museum or library had its own custom image viewer and API. This created "silos" where researchers couldn't easily compare images from two different institutions.

**IIIF solves this by providing:**
- **Interoperability:** Any IIIF-compliant viewer can display images from any IIIF-compliant repository.
- **Deep Zoom:** Smoothly pan and zoom into multi-gigapixel images without downloading the full file.
- **Rich Metadata:** Standardized way to describe the structure (e.g., pages in a book) and descriptive metadata.
- **Comparison & Annotation:** Scholars can "reunite" manuscripts scattered across the globe in a single workspace and annotate specific regions.

---

## 2. The API Suite (v3.0)

IIIF is not a single tool, but a collection of APIs:

### 2.1 Image API
Focuses on the **retrieval and delivery of pixels**.
- **Request Syntax:** `{scheme}://{server}{/prefix}/{identifier}/{region}/{size}/{rotation}/{quality}.{format}`
- **Parameters:**
  - `region`: `full`, `square`, or `x,y,w,h`.
  - `size`: `max`, `w,`, `,h`, or percentage.
  - `rotation`: `0`, `90`, `180`, `270`, or `!0` (mirroring).
  - `quality`: `default`, `color`, `gray`, `bitonal`.
  - `format`: `jpg`, `png`, `webp`, `tif`.

### 2.2 Presentation API
Focuses on the **structure and context**. It tells the viewer *how* these images relate to each other.
- **Manifest:** A JSON-LD file representing the object (e.g., a book).
- **Canvas:** A virtual container (a "page") where content (images, text) is "painted" via annotations.
- **Annotations:** In v3.0, everything is an annotation. An image is an annotation with a `painting` motivation.

### 2.3 Content Search API
Allows searching for **textual content within an object** (e.g., searching for a word in a digitized book).
- Returns results as `AnnotationPages`.
- Supports highlighting specific regions on the canvas where the text was found.

### 2.4 Change Discovery API
Allows systems to **discover and track changes** in IIIF resources across repositories.
- Uses **W3C Activity Streams**.
- Essential for aggregators (like Europeana or DPLA) to stay synced with institutional repositories.

---

## 3. The IIIF Ecosystem

### Image Servers (Back-end)
| Component | Cantaloupe | Loris | IIPImage |
| :--- | :--- | :--- | :--- |
| **Language** | Java | Python | C++ |
| **Pros** | Easiest setup, feature-rich, built-in server. | Native Python (WSGI), compliant. | Performance king, handles gigapixel/scientific files. |
| **Cons** | Slightly heavier footprint than C++. | Requires WSGI configuration. | Complex setup (requires FCGI-aware web server). |

### Viewers (Front-end)
| Viewer | Best For | Key Features |
| :--- | :--- | :--- |
| **Mirador** | Scholarly Research | Side-by-side comparison, workspace management, deep annotation tools. |
| **Universal Viewer** | Institutional Portals | Multimedia support (Audio/Video/3D/PDF), rich metadata display. |
| **OpenSeadragon** | Custom Development | Lightweight core for deep zoom rendering; used inside other viewers. |

---

## 4. Advanced: OCR & AI Integration

One of the most powerful uses of IIIF is managing OCR/HTR (Handwritten Text Recognition) data.

1.  **Transformation:** XML data (ALTO, hOCR) is converted into IIIF **Web Annotations**.
2.  **Spatial Mapping:** Each word/line is mapped to an `xywh` fragment on the IIIF Canvas.
3.  **Search-ability:** When a user searches for a term, the **Content Search API** returns these annotations, which the viewer then highlights on top of the original image.
4.  **Machine Learning:** Researchers can use IIIF manifests to programmatically pull high-quality training data for AI models (e.g., YOLO for object detection or CNNs for classification) directly from global repositories.

---

## 5. Real-World Use Cases
- **The Polonsky Foundation:** Digitized Greek and Hebrew manuscripts from the Vatican and Oxford, viewable side-by-side in Mirador.
- **Europeana / DPLA:** Aggregators that use Change Discovery to harvest millions of items.
- **The British Museum:** Provides high-res zooming via IIIF for its entire online collection.

## 6. Resources for Developers
- **Official Site:** [iiif.io](https://iiif.io)
- **IIIF Cookbook:** [iiif.io/cookbook](https://iiif.io/cookbook/) (Practical recipes for manifests)
- **Validation:** [presentation-validator.iiif.io](https://presentation-validator.iiif.io)
- **Training:** [training.iiif.io](https://training.iiif.io)
