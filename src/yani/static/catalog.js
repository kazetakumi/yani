// The catalog: the ONLY place a model-supplied component name becomes code.
// Hand-written static imports on purpose — the browser can't readdir
// catalogs/ at runtime, and keeping this table explicit (instead of a
// bundler glob or dynamic import) is a standing project decision: the
// catalog-lookup mechanism stays visible, not hidden in a reconciler.
// Adding a component = one folder + one import + one line here.

import { render as renderText } from './catalogs/Text/renderer.js';
import { render as renderImage } from './catalogs/Image/renderer.js';
import { render as renderIcon } from './catalogs/Icon/renderer.js';
import { render as renderVideo } from './catalogs/Video/renderer.js';
import { render as renderAudioPlayer } from './catalogs/AudioPlayer/renderer.js';
import { render as renderRow } from './catalogs/Row/renderer.js';
import { render as renderColumn } from './catalogs/Column/renderer.js';
import { render as renderList } from './catalogs/List/renderer.js';
import { render as renderCard } from './catalogs/Card/renderer.js';
import { render as renderTabs } from './catalogs/Tabs/renderer.js';
import { render as renderModal } from './catalogs/Modal/renderer.js';
import { render as renderDivider } from './catalogs/Divider/renderer.js';
import { render as renderButton } from './catalogs/Button/renderer.js';
import { render as renderTextField } from './catalogs/TextField/renderer.js';
import { render as renderCheckBox } from './catalogs/CheckBox/renderer.js';
import { render as renderChoicePicker } from './catalogs/ChoicePicker/renderer.js';
import { render as renderSlider } from './catalogs/Slider/renderer.js';
import { render as renderDateTimeInput } from './catalogs/DateTimeInput/renderer.js';
// Lesson block components (spec 0001 — the mentor port)
import { render as renderLessonHeader } from './catalogs/LessonHeader/renderer.js';
import { render as renderHeading } from './catalogs/Heading/renderer.js';
import { render as renderProse } from './catalogs/Prose/renderer.js';
import { render as renderDefinition } from './catalogs/Definition/renderer.js';
import { render as renderEquationBlock } from './catalogs/EquationBlock/renderer.js';
import { render as renderFigureSketch } from './catalogs/FigureSketch/renderer.js';
import { render as renderGraphBlock } from './catalogs/GraphBlock/renderer.js';
import { render as renderCodeBlock } from './catalogs/CodeBlock/renderer.js';
import { render as renderDataTable } from './catalogs/DataTable/renderer.js';
import { render as renderExplainBack } from './catalogs/ExplainBack/renderer.js';
import { render as renderPracticeChecklist } from './catalogs/PracticeChecklist/renderer.js';
import { render as renderQuizBlock } from './catalogs/QuizBlock/renderer.js';
import { render as renderSummaryBlock } from './catalogs/SummaryBlock/renderer.js';
import { render as renderTreeLocator } from './catalogs/TreeLocator/renderer.js';
// Checkpoint components (spec 0002 — the lesson dialogue)
import { render as renderChipRow } from './catalogs/ChipRow/renderer.js';
import { render as renderPromptInput } from './catalogs/PromptInput/renderer.js';

export const CATALOG = {
  Text: renderText,
  Image: renderImage,
  Icon: renderIcon,
  Video: renderVideo,
  AudioPlayer: renderAudioPlayer,
  Row: renderRow,
  Column: renderColumn,
  List: renderList,
  Card: renderCard,
  Tabs: renderTabs,
  Modal: renderModal,
  Divider: renderDivider,
  Button: renderButton,
  TextField: renderTextField,
  CheckBox: renderCheckBox,
  ChoicePicker: renderChoicePicker,
  Slider: renderSlider,
  DateTimeInput: renderDateTimeInput,
  LessonHeader: renderLessonHeader,
  Heading: renderHeading,
  Prose: renderProse,
  Definition: renderDefinition,
  EquationBlock: renderEquationBlock,
  FigureSketch: renderFigureSketch,
  GraphBlock: renderGraphBlock,
  CodeBlock: renderCodeBlock,
  DataTable: renderDataTable,
  ExplainBack: renderExplainBack,
  PracticeChecklist: renderPracticeChecklist,
  QuizBlock: renderQuizBlock,
  SummaryBlock: renderSummaryBlock,
  TreeLocator: renderTreeLocator,
  ChipRow: renderChipRow,
  PromptInput: renderPromptInput,
};
