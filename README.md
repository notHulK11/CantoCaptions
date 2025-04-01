# CantoCaptions

## Overview
This is a project that aims to collect and create accurate written Cantonese subtitles for educational purposes. Accurate subtitles are those that match the spoken dialogue. Written Cantonese is the written form of the Cantonese language that contrasts with what is typically used, known as Standard Written Chinese. Written Cantonese subtitles are seldom used but are very powerful learning resources.

If you would like to contribute to transcripts or subtitles, make a donation, find out about current projects, or simply learn more, please join our [Discord](https://discord.gg/Eh7XCENw4t) server.

> [!IMPORTANT]  
> Since many of the characters used in these subtitles fall outside the coverage of typical fonts, it is <ins>**HIGHLY**</ins> recommended that you install a Cantonese specific font. We recommend installing one of the fonts from https://github.com/chiron-fonts/chiron-hei-hk.

## Table of Contents

- [Subtitle Style Guide](#Subtitle-Style-Guide)
	- [Formatting](#Formatting)
	- [Timing](#Timing)
	- [Punctuation](#Punctuation)
	- [Untranscribed Speech](#Untranscribed-Speech)
- [Character Conventions](#Character-Conventions)
	- [Sentence Final Particles](#sentence-final-particles句尾助詞)
	- [Affixes](#affixes詞綴)
	- [Interjections](#interjections感嘆詞)
	- [Character Variants](#Character-Variants)
	- [Other](#Other)

## Subtitle Style Guide

This section details how the subtitles should look. In general, Traditional characters are used as opposed to simplified characters, since they can always be converted to the latter with relative ease.

### General Guiding Principles

The goal of these subtitles is to be as useful to learners as possible. The goal is *NOT* to be as faithful to the literal utterances as spoken by the actors or voice actors. Put another way, we want to capture intended, correct speech, and not misspeaks or agrammatical speech. Furthermore, while the subtitles do aim at comprehensive coverage of what is said, grunts, yells, laughter, and miscellaneous expressive noises should in general be transcribed sparingly and, in some cases, not at all. Such subtitles, broadly speaking, don't contribute to building understanding of the language. To this end, it is recommended to transcribe most interjections only in so far as they are followed by or form part of a longer utterance.

### Formatting
- .srt format
- single line max length is 18 characters

This .srt subtitle format is chosen because of its wide-ranging compatibility especially with language learning tools such as pop-up dictionaries.

### Timing
- lines can appear 0-30ms before the start of the speech
- lines can slightly trail speech (~0-60ms) after the end of the speech
- lines that end within roughly ~20ms of a scene change should be synced with the scene change
- lines with a length of 3 characters or more need a minimum duration of 750ms
	- this can be shorter in the case of a scene change or based on other factors such as lots of speech or interrupted speech
- lines with a length of 2 or fewer characters don't have to follow that minimum

### Punctuation

| Explanation                                                                                                                                                 | Examples                                |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------- |
| Written or background info is enclosed in Chinese parentheses.                                                                                              | （三年前）                                   |
| The titles (of episodes, works, etc.) are enclosed in Chinese double arrow brackets.                                                                        | 《進擊的巨人》                                 |
| Secondary titles are separated with a Chinese colon.                                                                                                        | 《哈利波特：神秘的魔法石》                           |
| Episode titles are enclosed with Chinese square brackets.                                                                                                   | ［戰士］                                    |
| Miscellaneous titles, such as in on-screen text are enclosed with lenticular brackets.                                                                      | 【Sub Topic】                             |
| A Chinese comma is placed after all SFP, except when followed by 你 without a pause.                                                                         | ❌好啦我明喇。<br>✅好啦，我明喇<br>❌好春廢啊，你<br>✅好春廢啊你 |
| Multiple speaker dialogue uses two lines and dialogue that begins with a hyphen without a following space.                                                  | -speaker 1<br>-speaker 2                |
| Direct speech styling uses Chinese colon followed by dialogue enclosed in left and right Chinese quotation characters.                                      | 我媽媽話：「唔准去嗰度」                            |
| When a question is followed by the name of who is being addressed then the question mark is used as the separator as opposed to a comma and a question mark | ❌你仲喺度，阿明？<br>✅你仲喺度？阿明                   |
| Only 1 Chinese ellipsis character is used (never 2 as in ……).                                                                                               | ❌……<br>✅…                               |
| When an utterance is repeated, transcribe only 1 instance with a trailing Chinese ellipsis character.                                                       | ❌ 喂喂喂<br>✅ 喂…                           |
| In the case of interrupted speech, a Chinese ellipsis character is used to mark where the speaker is cut off and a new line begins with the new speech.     | -點解你…<br>-唔知啊                           |
| In the case of trailing  speech, a Chinese ellipsis character is used.                                                                                      | ❌佢唔可以嘅話~~<br>✅佢唔可以嘅話…                   |
| In the case of stammering, the start is separated by a Chinese ellipsis, but this is only done once.                                                        | ❌只只不過<br>❌只…只…只不過<br>✅只…只不過             |
| When listing with 同 or 同埋, Chinese list comma is used on the elements that are not connected with the conjunction.                                          | A、B、C同埋D                                |
| Subtitles never end in a period and Chinese period is never used.                                                                                           | ❌我個名叫Tom。<br>✅我個名叫Tom                   |
| The middle period is never used.                                                                                                                            | ❌哈利·波特<br>✅哈利波特                         |
| Italics are never used.                                                                                                                                     |                                         |

### Untranscribed Speech
In general, these subtitles are a learning resource. The goal is not to transcribe verbatim all utterances in their entirety. The goal is have a complete subtitle that contains information useful to the learner. We do not want to include very minor, incidental speech/sounds, or unintentionally incorrect speech. Sentence Final Particles are transcribed as accurately as possible to benefit the learner.

| Speech                                                                                                                                                                                                                                                                          | Example         |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| Brief "uh" sounds in the middle of speech are not transcribed.                                                                                                                                                                                                                  |                 |
| The Chinese exclamation point is used sparingly. For example, for exceptionally loud/declarative yells or for emphasis among quieter speech, such as when calling someone's name. Even if a character is yelling, it's discouraged to end every line with an exclamation point. |                 |
| Miscellaneous grunts, yells, screams, and the like are not transcribed.                                                                                                                                                                                                         |                 |
| Ah, oh, hmm, huh, mhmm and other acknowledgement noises are transcribed sparingly and primarily in the case that they form part of other utterances.                                                                                                                            | ❌吓？<br>✅吓？你講咩啊？ |


## Character Conventions
The aim behind establishing conventions is to promote consistency that will enhance learning and further promote written Cantonese. These conventions go out of their way to promote unambiguous character usage in many instances.


> [!NOTE]
> The conventions have been evolving over time and many of the existing subtitles have not been updated in accordance with the latest standards.


### Sentence Final Particles｜句尾助詞

| **Syllable＼Tone** | **1** | **2** | **3** | **4** | **5** | **6** |
| ----------------- | ----- | ----- | ----- | ----- | ----- | ----- |
| aa                | 吖     | 嗄     | 啊     | 呀     | 咓     | 𠻺    |
| aak               |       |       | 𡅅    |       |       |       |
| baa               |       | 罷     |       |       |       |       |
| bo                |       |       | 噃     |       |       |       |
| gaa               | 𠺢    | 𠿪    | 㗎     | 嘎     |       |       |
| gaak              |       |       | 𠺝    |       |       |       |
| ge                |       | 𠸏    | 嘅     |       |       |       |
| gwaa              |       |       | 啩     |       |       |       |
| haa               |       | 吓     |       |       |       | 下     |
| he                |       | 嚱     |       |       |       |       |
| ho                |       | 嗬     |       |       |       |       |
| laa               | 啦     |       | 喇     | 嗱     |       |       |
| laak              |       |       | 嘞     |       |       |       |
| le                | 呢     |       |       | 咧     | 哩     |       |
| lo                | 囖     |       | 咯     | 囉     |       |       |
| lok               |       |       | 嚛     |       |       |       |
| lu                |       |       | 嚕     |       |       |       |
| maa               |       |       | 嘛     |       | 嗎     |       |
| me                | 咩     |       |       |       |       |       |
| tim               | 𠻹    |       |       |       |       |       |
| waa               |       |       |       |       | 哇     |       |
| wo                |       |       | 喎     | 啝     | 𡁜    |       |
| zaa               | 吒     |       | 咋     | 喳     | 𠾵    |  咤   |
| ze                | 啫     |       |       |       |       |       |
| zek               | 唧     |       |       |       |       |       |

In the interest of clarity, the contraction aa6 maa5 into maa5 should be written out in full: 𠻺嗎.

| Jyutping｜粵拼 | Honzi｜漢字 |
| ------------- | ---------- |
| a1 maa3       | 吖嘛         |
| a1 naa4       | 吖嗱         |
| a3 ho2        | 啊嗬         |
| a3 haa2       | 啊吓         |
| a6 maa5       | 𠻺嗎        |
| baa2 laa1     | 罷啦         |
| ga1 maa3      | 𠺢嘛        |
| ga3 wo3       | 㗎喎         |
| ge3 ze1       | 嘅啫         |
| ge3 zek1      | 嘅唧         |
| ha6 waa5      | 下哇         |
| la1 maa3      | 啦嘛         |
| la3 wo3       | 喇喎         |
| za1 maa3      | 吒嘛         |

### Affixes｜詞綴
| Jyutping｜粵拼 | Honzi｜漢字 | Examples｜例子           |
| ----------- | -------- | --------------------- |
| aa3         | 阿        | **阿**爸、**阿**伯、**阿**明  |
| can1        | 親        | **親**隻腳、跌**親**        |
| dei2        | 地        | 嘛嘛**地**、悶悶**地**       |
| di1         | 啲        | 細**啲**、靚**啲**         |
| dou2        | 到        | 見**到**、做唔**到**        |
| faan1       | 返        | 好**返**、畀**返**你        |
| gam2        | 噉        | **噉**樣、係**噉**         |
| gam3        | 咁        | **咁**多、**咁**耐         |
| haa5        | 下        | 睇**下**、試**下**、行行**下** |
| kiu1        | Q        | 痴**Q**線、做乜**Q**啊      |
| maai4       | 埋        | 同**埋**、畀**埋**、交**埋**  |
| saai3       | 晒        | 多謝**晒**、辛苦**晒**       |

### Interjections｜感嘆詞

| Jyutping｜粵拼             | Honzi｜漢字 | Explanation｜解釋                     |
| ----------------------- | -------- | ---------------------------------- |
| aai1, aai2              | 唉        |                                    |
| ai1 jaa3/5/6, ai1 jaak3 | 哎吔       |                                    |
| ce1                     | 唓        | "tsk"                              |
| e2, ei2                 | 欸        |                                    |
| e4, e6                  | 誒        | "uh"                               |
| hei1                    | 嘿        | as a greeting / shows satisfaction |
| hei5                    | 唏        | shows discontent                   |
| hng6                    | 哼        | "hmph"                             |
| ji2                     | 咦        |                                    |
| m2, m3, m6              | 嗯        | "hmm"; "um"; "mhmm"                |
| naa4                    | 嗱        | "look"; call for attention         |
| o1                      | 喔        |                                    |
| o2, o3, o4, o5, o6      | 哦        |                                    |
| oi2, oi3                | 噯        | variant of 喂                       |
| ou3                     | 噢        |                                    |
| syu4                    | 𭉝       | "shh"                              |
| u1                      | 嗚        | "ooo"; sound of interest/wonder     |
| waa1                    | 哇        | "wah"; sound of crying             |
| waa3, waa4              | 嘩        | "wow"                              |
| wai2, wai3              | 喂        |                                    |
### Character Variants
Where applicable, the Hong Kong variant of characters is chosen.

| ✅ Selected Variant | ❌ Other Variants | Jyutping |
| ---------------- | -------------- | -------- |
| 為                | 爲              | wai4     |
| 揾                | 搵              | wan2     |
| 揀                | 㨂              | gaan2    |
| 説                | 說              | syut3    |
| 牀                | 床              | cong4    |
| 群                | 羣              | kwan4    |
| 裏                | 裡              | leoi5    |
| 麪                | 麵              | min6     |
| 教                | 敎              | gaau3    |
| 秘                | 祕              | bei3     |
| 市                | 巿              | si5      |
| 眾                | 衆              | zung3    |
| 濕                | 溼              | sap1     |
| 雞                | 鷄              | gai1     |
| 告                | 吿              | gou3     |
| 污                | 汙              | wu1      |
| 泄                | 洩              | sit3     |
| 罵                | 駡              | maa6     |
| 鏽                | 銹              | sau3     |
| 鏽                | 銹              | sau3     |
| 鈎                | 鉤              | ngau1    |
| 衞                | 衛              | wai6     |
| 葱                | 蔥              | cung1    |
| 豔                | 艷              | jim6     |
| 藥                | 葯              | joek6    |
| 匯                | 滙              | wui6     |
| 啓                | 啟              | kai2     |
| 獎                | 奬              | zoeng2   |

### Other
| ✅ Selected Variant | ❌ Other Variants | Jyutping                       | Explanation               |
| ---------------- | -------------- | ------------------------------ | ------------------------- |
| 畀                | 俾              | bei2                           |                           |
| 搞                | 攪              | gaau2                          | 指「做」                   |
| 打搞晒            | 打攪晒            | daa2 gaau2 saai3               |                           |
| 攰                | 癐              | gui6                           |                           |
| 郁                | 喐              | juk1                           |                           |
| 𦧷                | 舔、lem         | lem2                           | 用條脷輕輕力掃             |
| 唔單止             | 唔單只            | m4 daan1 zi2                   |                           |
| 唔止               | 唔只             | m4 zi2                         |                           |
| 而家               | 宜家             | ji4 gaa1                       |                           |
| 唔使               | 唔駛             | m4 sai2                        |                           |
| 即係               | 姐係、啫係、唧係    | zik1 hai6                      |                           |
| 淨係               | 剩係             | zing6 hai6                     |                           |
| 呢個               | 依個             | ni1 go3                        |                           |
| 依個               | 𠵱個            | ji1 go3                        |                           |
| 傾偈               | 傾計             | king1 gai2                     |                           |
| 抌                | 丼、揼            | dam2                           |                           |
| 𢱕               | 溚、揼            | dap6                           |                           |
| 揼                | 耽              | dam1, dam3, dam6               |                           |
| 着                | 著              | zoek3, zoek6                   |                           |
| 著                | 着              | zyu3                           |                           |
| 兇                | 凶              | hung1                          | 兇猛、兇手、兇某人                 |
| 凶                | 凶兆             | hung1                          | 泛指一啲不祥嘅嘢                  |
| 證                | 証              | zing3                          |                           |
| 㧻                | 篤、督、厾          | duk1                           | 係動詞，指「刺」、「戳」              |
| 涿                | 篤              | duk1                           | 係量詞，指「一涿屎」或「一涿尿」          |
| 督                | 篤              | duk1                           | 用於「監督」、「都督」等              |
| 篤                | 督              | duk1                           | 用於「篤信」、「篤定」等              |
| 㞘                | 𡰪             | duk1                           | 指最尾或末端，例如「行到㞘」            |
| 邊                | 便              | bin1, bin6                     | 用於「邊度」、「入邊」               |
| 弊喇               | 𡃇喇            | bai6 laa3                      |                           |
| 瀨屎、瀨尿            | 賴屎、賴尿          | laai6 si2, laai6 niu6          |                           |
| 鬥                | 鬭              | dau3                           | 1. 對打 2. 分勝負 3. 花工夫去整一樣嘢           |
| 抖                | 鬥              | dau3                           | 摸；掂                       |
| 唞                | 抖              | tau2                           | 休息；歇息                     |
| 走夾唔唞             | 走夾唔抖           | zau2 gaap3 m4 tau2             |                           |
| 早唞               | 早抖             | zou2 tau2                      |                           |
| 攤唞               | 攤抖             | taan1 tau2                     |                           |
| 有氣冇碇唞            | 有氣冇碇抖          | jau5 hei3 mou5 deng6 tau2      |                           |
| 唞涼               | 抖涼             | tau2 loeng4                    |                           |
| 唞暑               | 抖暑             | tau2 syu2                      |                           |
| 唞氣               | 抖氣             | tau2 hei3                      |                           |
| 唞大氣              | 抖大氣            | tau2 daai6 hei3                |                           |
| 渣                | 鮓、謯、苴          | zaa2                           |                           |
| 撳                | 㩒              | gam6                           |                           |
| 拗                | 詏              | aau3                           | 同人爭執                      |
| 好嘢               | 好耶             | hou2 je5                       |                           |
| 𢯎               | R、摳、撓、𢲷       | ngaau1                         |                           |
| 𡃴               | 除              | ceoi4                          | 臭味                        |
| 枝                | 支              | zi1                            | 指植物或木嘅嘢                 |
| 度過               | 渡過             | dou6 gwo3                      |                           |
| 保佑               | 保祐             | bou2 jau6                      |                           |
| 不嬲               | 不溜、不留          | bat1 lau1, bat1 lau2           | 一直                        |
| 𢫏               | 冚              | kam2                           | 遮住                        |
| 扻                | 冚              | kam2                           | 掌摑                        |
| 撼                | 扻              | ham2                           | 撞到                        |
| 冚                |                | kam2                           | 用嚟遮住底下嘅嘢（量詞：個）            |
| 冚                |                | ham6                           | 全部; 接口閂得實                 |
| 撼                | 冚              | ham6                           | 引起強烈感受                    |
| 爹哋               | 爹地、爹啲          | de1 di4                        |                           |
| BB               | 啤啤             | bi4 bi1                        |                           |
| 錔                | 搭、塔            | taap3                          | 用手銬；鎖                     |
| 𠹷               | 哦              | ngo4                           | 好煩噉樣批評或者抱怨                |
| 髹                | 油              | jau4                           | 用油漆或顏料填上顏色、覆蓋表面           |
| 𨈇               | 𨂾、揇、檻         | laam3                          |                           |
| 係噉意              | 係噉咦            | hai6 gam2 ji2                  |                           |
| 吽哣               | 吽竇、吽逗          | ngau6 dau6                     |                           |
| 發吽哣              | 發吽逗、發吽竇        | faat3 ngau6 dau6               |                           |
| 讕                | 懶              | laan2                          | 扮做；自命                     |
| 莫名其妙             | 莫明其妙           | mok6 ming4 kei4 miu6           |                           |
| 大部份              | 大部分            | daai6 bou6 fan6                |                           |
| 過份              | 過分            | gwo3 fan6              |                           |
| 咭                | 卡              | kaat1                          | 例如：信用卡                    |
| 卡                | car, carat, 黐住 | kaat1                          |                           |
| 朦                | 矇、蒙            | mung4                          | 朦朧；模糊                     |
| 賜予               | 賜與             | ci3 jyu5                       |                           |
| 抰                | 揚              | joeng2                         | 揮動一件軟軟地嘅物件                |
| 揚                |                | joeng4                         | 傳揚；張揚                     |
| 哽                | 啃、鯁、骾          | kang2                          | 夾硬吞落喉嚨；有啲嘢食卡咗喺喉嚨          |
| 𬒔               | 哽              | ang2                           | 一啲突起嘅嘢頂住，令人唔舒服或痛          |
| 濕𣲷𣲷            | 濕立立            | sap1 nap6 nap6                 |                           |
| 嗱嗱聲              | 拿拿聲、啦啦聲        | laa4 laa2 seng1                |                           |
| 倔                | 掘              | gwat6                          | 執著；鈍                      |
| 籮柚               | 囉柚             | lo1 jau2                       |                           |
| 㓟                | 批、𠜱           | pai1                           | 1. 刀法 2. 削走啲嘢             |
| 唯有               | 惟有             | wai4 jau5                      |                           |
| 惜                | 錫              | sek3                           | 1. 愛、關心、緊張 2. 用嘴唇掂另一個人嘅身體 |
| 錫                |                | sek6                           | 一種金                       |
| 冧                | 㨆              | lam1                           | 1. 甜蜜、氹人 2. 花植物嘅一部分 3. 冧歌 |
| 㨆                | 冧              | lam3, lam6                     | 1. 跌倒 2. 堆起 3. 連續         |
| 嘺                | 橋、蹺、巧          | kiu2                           | 表示咁啱                      |
| 騎呢怪              | 奇離怪            | ke4 le4 gwaai3, ke4 le4 gwaai2 |                           |
| 淝                | fea、啡、fe       | fe4                            |                           |
| 林沈               | 淋糝、林審          | lam4 sam2                      |                           |
| 蕃茄               | 番茄             | faan1 ke2                      |                           |
| 拮                | 㓤              | gat1                           | 用尖而幼細嘅嘢插入                 |
| 咖哩雞              | 咖喱雞            | gaa3 lei1 gai1                 |                           |
| 𦧲              | lur             | loe1*2                         |                           |
| 掹                | 擝              | mang1                          |                           |
| 拈                | lim、令、捻        | lim1                           | 紙嘅單位，通常指500張              |
| 捻                | 掐              | nin2                           | 雙手或者多隻手指夾住一嚿嘢             |
| 吼住               | 睺住、喉住          | hau1 zyu6, hau4 zyu6           | 望住                        |
| 飆                | 標              | biu1                           |                           |
| 故仔、故事            | 古仔、古事          | gu3 zai2, gu3 si6              |                           |
| 囈                | 𠼮、誽、𠱓        | ngai1, ai1                     | 央求                        |
| 氹                | 𠱁、𧨾          | tam3                           | 1. 令人開心 2. 哄騙             |
| 凼                | 氹              | tam5                           | 1. 水喺凹陷地方 2. 陷阱           |
| 蓆                | 席              | zek6                           | 用竹片等材料製成嘅墊                |
| 席                |                | zik6                           |                           |
| 𥄫               | gup            | gap6                           | 1. 偷窺 2. 凝視               |
| 㨃                | 隊              | deoi2                          | 1. 捅 2. 短時間內攝取好多嘢         |
| 盟塞               | 盲塞、萌塞          | mang4 sik1, mang4 sak1         |                           |
| 軟腍腍              | 軟淋淋            | jyun5 nam4 nam4                |                           |
| 倔頭路              | 掘頭路            | gwat6 tau4 lou6                |                           |
| 𣲷懦              | 𥹉懦            | nap6 no6                       |                           |
| 䁓                | 裝、𥅾、𥊙        | zong1                          | 偷窺                        |
| 韞                | 困              | wan3                           | 局限喺一個地方之內，唔出嚟             |
| 係咁歹              | 係咁大            | hai6 gam3 daai2                |                           |
| urk              | 嗝              | oet4, oet6, oek4               |                           |
| 嘍              | 摟              | lau3               |                           |
| 篋              | gip、喼              | gip1               |                           |
| 剁              | 斫、斵            | doek6              |                           |
