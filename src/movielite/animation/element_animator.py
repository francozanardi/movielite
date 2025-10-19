from typing import Optional, List
from pycaps.common import ElementType, EventType, Document, WordClip
from pycaps.tag import TagCondition
from pycaps.selector import WordClipSelector
from .animation import Animation

class ElementAnimator:

    def __init__(self, animation: Animation, when: EventType, what: ElementType, tag_condition: Optional[TagCondition] = None) -> None:
        self._animation: Animation = animation
        self._when: EventType = when
        self._what: ElementType = what
        self._tag_condition: Optional[TagCondition] = tag_condition

    def run(self, document: Document) -> None:
        clips = self._filter_clips(document)
        for clip in clips:
            offset = self.__get_time_offset(clip)
            self._animation.run(clip, offset, self._what)

    def _filter_clips(self, document: Document) -> List[WordClip]:
        selector = WordClipSelector().filter_by_time(self._when, self._what, self._animation._duration, self._animation._delay)
        if self._tag_condition:
            selector = selector.filter_by_tag(self._tag_condition)
        return selector.select(document)

    def __get_time_offset(self, clip: WordClip) -> float:
        if self._when == EventType.ON_NARRATION_STARTS:
            return self.__get_on_start_offset(clip)
        elif self._when == EventType.ON_NARRATION_ENDS:
            return self.__get_on_end_offset(clip)
    
    def __get_on_start_offset(self, clip: WordClip) -> float:
        start_time = 0
        if self._what == ElementType.WORD:
            start_time = clip.get_word().time.start
        elif self._what == ElementType.LINE:
            start_time = clip.get_line().time.start
        elif self._what == ElementType.SEGMENT:
            start_time = clip.get_segment().time.start

        return clip.media_clip.start - start_time - self._animation._delay

    def __get_on_end_offset(self, clip: WordClip) -> float:
        end_time = 0
        if self._what == ElementType.WORD:
            end_time = clip.get_word().time.end
        elif self._what == ElementType.LINE:
            end_time = clip.get_line().time.end
        elif self._what == ElementType.SEGMENT:
            end_time = clip.get_segment().time.end
        return -(end_time - self._animation._duration - self._animation._delay - clip.media_clip.start)
