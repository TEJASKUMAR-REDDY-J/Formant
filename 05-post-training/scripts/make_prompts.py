"""Write prompts/spoken-v0.jsonl: the same ten everyday situations in seven language settings.

These are drafts by non-native authors. Nothing is scored on them until a native speaker has reviewed the line and set
native_reviewed to true here. The full set (100 per language) is written with native speakers.
"""
import json
import pathlib

TOPICS = ["weather", "price", "phone_number", "date", "recipe", "directions", "advice", "explain", "time", "chat"]
P = {
    "en": ["Will I need an umbrella tomorrow?", "How much is a kilo of tomatoes these days?", "What number do I call for an ambulance?",
           "When is Republic Day?", "How do I make ginger tea?", "How do I get to the railway station from the bus stand?",
           "I can't sleep at night. What should I do?", "Why is the sky blue?", "How long does it take from Delhi to Jaipur by train?",
           "I had a really tiring day today."],
    "hi": ["कल छाता लेकर जाना पड़ेगा क्या?", "आजकल टमाटर कितने रुपये किलो है?", "एम्बुलेंस के लिए कौन सा नंबर लगाऊँ?", "गणतंत्र दिवस कब होता है?",
           "अदरक वाली चाय कैसे बनाते हैं?", "बस अड्डे से रेलवे स्टेशन कैसे जाऊँ?", "रात को नींद नहीं आती, क्या करूँ?", "आसमान नीला क्यों होता है?",
           "दिल्ली से जयपुर ट्रेन में कितना समय लगता है?", "आज बहुत थका देने वाला दिन था।"],
    "bn": ["কাল কি ছাতা নিয়ে বেরোতে হবে?", "আজকাল টমেটো কত টাকা কিলো?", "অ্যাম্বুলেন্সের জন্য কোন নম্বরে ফোন করব?", "প্রজাতন্ত্র দিবস কবে?",
           "আদা চা কীভাবে বানায়?", "বাস স্ট্যান্ড থেকে রেল স্টেশন কীভাবে যাব?", "রাতে ঘুম আসে না, কী করব?", "আকাশ নীল কেন?",
           "দিল্লি থেকে জয়পুর ট্রেনে কত সময় লাগে?", "আজ খুব ক্লান্তিকর একটা দিন গেল।"],
    "mr": ["उद्या छत्री घेऊन जावी लागेल का?", "आजकाल टोमॅटो किती रुपये किलो आहेत?", "रुग्णवाहिकेसाठी कोणता नंबर लावू?", "प्रजासत्ताक दिन कधी असतो?",
           "आल्याचा चहा कसा करतात?", "बस स्थानकापासून रेल्वे स्टेशनला कसं जाऊ?", "रात्री झोप येत नाही, काय करू?", "आकाश निळं का दिसतं?",
           "दिल्लीहून जयपूरला ट्रेनने किती वेळ लागतो?", "आजचा दिवस खूप थकवणारा होता."],
    "ta": ["நாளைக்கு குடை எடுத்துட்டு போகணுமா?", "இப்போ தக்காளி கிலோ எவ்வளவு?", "ஆம்புலன்ஸுக்கு எந்த நம்பருக்கு கூப்பிடணும்?", "குடியரசு தினம் எப்போ வரும்?",
           "இஞ்சி டீ எப்படி போடறது?", "பஸ் ஸ்டாண்டிலிருந்து ரயில்வே ஸ்டேஷனுக்கு எப்படி போகணும்?", "ராத்திரி தூக்கம் வரலை, என்ன பண்ணலாம்?", "வானம் ஏன் நீலமா இருக்கு?",
           "டெல்லியிலிருந்து ஜெய்ப்பூருக்கு ரயில்ல எவ்வளவு நேரம் ஆகும்?", "இன்னைக்கு ரொம்ப களைப்பான நாள்."],
    "te": ["రేపు గొడుగు తీసుకెళ్ళాలా?", "ఈ మధ్య టమాటా కిలో ఎంత?", "అంబులెన్స్ కోసం ఏ నంబర్‌కి ఫోన్ చేయాలి?", "గణతంత్ర దినోత్సవం ఎప్పుడు?",
           "అల్లం టీ ఎలా చేస్తారు?", "బస్ స్టాండ్ నుంచి రైల్వే స్టేషన్‌కి ఎలా వెళ్ళాలి?", "రాత్రి నిద్ర పట్టడం లేదు, ఏం చేయాలి?", "ఆకాశం నీలంగా ఎందుకు ఉంటుంది?",
           "ఢిల్లీ నుంచి జైపూర్‌కి రైల్లో ఎంత సమయం పడుతుంది?", "ఈ రోజు చాలా అలసటగా గడిచింది."],
    "hi-en": ["Kal umbrella leke jaana padega kya?", "Aajkal tomato kitne rupaye kilo hai?", "Ambulance ke liye kaunsa number call karun?", "Republic Day kab hota hai?",
              "Ginger chai kaise banate hain?", "Bus stand se railway station kaise jaun?", "Raat ko neend nahi aati, kya karun?", "Sky blue kyun hota hai?",
              "Delhi se Jaipur train mein kitna time lagta hai?", "Aaj ka din bahut tiring tha yaar."],
}

if __name__ == "__main__":
    out = pathlib.Path(__file__).resolve().parents[1] / "prompts" / "spoken-v0.jsonl"
    out.parent.mkdir(exist_ok=True)
    rows = []
    for lang, texts in P.items():
        assert len(texts) == len(TOPICS), lang
        rows += [{"id": f"{lang}-{t}", "lang": lang, "topic": t, "prompt": x, "native_reviewed": False} for t, x in zip(TOPICS, texts)]
    out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    print(len(rows), "prompts ->", out)
