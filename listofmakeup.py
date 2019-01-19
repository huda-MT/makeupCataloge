from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup1 import MakeUp, Base, MakeUpItem, User

engine = create_engine('sqlite:///makeupcatalog.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

# Create dummy user
User1 = User(name="huda ", email="huda51@windowslive.com")
session.add(User1)
session.commit()

# list for Face
group1 = MakeUp(user_id=1, name="Face")
session.add(group1)
session.commit()

# foundation
foundation = MakeUpItem(user_id=1, name="Foundation",
                        group="Face",
                        description="Evens out the skin colour" +
                        ".Usually a liquid, cream, or powder. Of the all " +
                        "the types of makeup,foundation is often the" +
                        "starting block for makeup use.",
                        price="39$",
                        makeup=group1
                        )


session.add(foundation)
session.commit()

# concealer
concealer = MakeUpItem(
                        user_id=1, name="Concealer",
                        group="Face",
                        description="Covers any imperfections of the skin" +
                        "such as blemishes and marks.",
                        price="30$",
                        makeup=group1)

session.add(concealer)
session.commit()

# list for Eyes
group2 = MakeUp(user_id=1, name="Eyes")
session.add(group2)
session.commit()

# mascara
mascara = MakeUpItem(
    user_id=1,
    name="Mascara",
    group="eyes",
    description="Darkens, lengthens, and thickens the eyelashes.",
    price="65$",
    makeup=group2
    )

session.add(mascara)
session.commit()

# eyebrow_pencil
eyebrow_pencil = MakeUpItem(
    user_id=1,
    name="Eyebrow Pencil",
    group="eyes",
    description="Defines the brows.",
    price="21$",
    makeup=group2
    )

session.add(eyebrow_pencil)
session.commit()


# list for Lips
group3 = MakeUp(user_id=1, name="Lips")
session.add(group3)
session.commit()

# lipstick
lipstick = MakeUpItem(
    user_id=1,
    name="Lipstick",
    group="Lips",
    description="Lipstick is a cosmetic product containing pigments," +
    "oils,waxes and emollients that applies color," +
    " texture, and protection to the lips.",
    price="14$",
    makeup=group3
    )

session.add(lipstick)
session.commit()

# lip_gloss
lip_gloss = MakeUpItem(
    user_id=1,
    name="Lip Gloss",
    group="Lips",
    description="Lip gloss is a product used primarily to give lips a glossy" +
    "luster and sometimes subtle color",
    price="14$",
    makeup=group3
    )

session.add(lip_gloss)
session.commit()


# list for cheek Group
group4 = MakeUp(user_id=1, name="Cheek")
session.add(group4)
session.commit()

# blush
blush = MakeUpItem(
    user_id=1,
    name="Blush",
    group="Cheek",
    description="A type of cosmetic to redden the cheeks so as to provide " +
    "a more youthful appearance and to emphasize the cheekbones.",
    price="30$",
    makeup=group4
    )

session.add(blush)
session.commit()

# highlighter
highlighter = MakeUpItem(
    user_id=1,
    name="Highlighter",
    group="Cheek",
    description="Used to draw attention to the high points of the face " +
    "as well as to add glow to the face. ",
    price="28$",
    makeup=group4
    )

session.add(highlighter)
session.commit()


print "added group items!"
