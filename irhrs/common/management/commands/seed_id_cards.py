from django.core.exceptions import ValidationError
from django.core.management import BaseCommand

from irhrs.common.models import IdCardSample

ID_CARD_SAMPLES = [(
    'Sample 1',
    """
    <div class="id-card-holder">
        <div class="id-card" id="id-card">
          <div class="header">
            <img id="orgLogo" src="http://untp.realhrsoft.com/static/img/logo/logo-with-tag.png">
          </div>
          <div class="photo">
            <img 
              id="userPP" 
              style="border-radius: 100%"
              src="https://i0.wp.com/w.media/wp-content/uploads/2018/01/placeholderhead.jpg"
            >
          </div>
          <h2 id="userName">Name Here</h2>
          <h4 id="userDesignation">Designation Here</h4>
          <h4> Ph: <span id="userPhone"> 9812345678 </span></h4>
          <br>
          <hr>
          <br>
          <p id="orgAddress"> Address Here <p>
          <p>Ph: <span id="orgPhone">9812345678</span> </p>
          <p> Email: <span id="orgEmail">example@email.com </span> </p>
          <p> Issued On: <span id="issuedOn"> 2010-01-01 </span></p>
          <div class="sign">
            <img
              id="signature" src="https://qph.fs.quoracdn.net/main-qimg-2248bdd01f82b9fb9becdc4bd9a92c53" 
              style="width:100px; height:50px;">
          </div>
        </div>
      </div>
      <style>
        .id-card-holder {
          width: 225px;
          height: 387px;
          padding: 4px;
          margin: 0 auto;
          background-color: #1f1f1f;
          border-radius: 5px;
          position: relative;
        }
        .id-card {
          background-color: #fff;
          background-size: cover;
          padding: 10px;
          border-radius: 10px;
          text-align: center;
          box-shadow: 0 0 1.5px 0px #b9b9b9;
        }
        .id-card img {
          margin: 0 auto;
        }
        .header img {
          height: 25px;
          margin-top: 15px;
        }
        .photo img {
          height: 75px;
          margin-top: 15px;
        }
        h2 {
          font-size: 15px;
          margin-top: 5px;
        }
        h3 {
          font-size: 12px;
          margin: 2.5px 0;
          font-weight: 300;
        }
        h4{
          font-size: 10px;
          margin: 0;
          font-weight: 300;
          color: grey;
        }
        .qr-code img {
          width: 50px;
        }
        p {
          font-size: 8px;
          margin: 2px;
        }
        .id-card-hook {
          background-color: #000;
          width: 70px;
          margin: 0 auto;
          height: 15px;
          border-radius: 5px 5px 0 0;
        }
        .id-card-hook:after {
          content: '';
          background-color: #d7d6d3;
          width: 47px;
          height: 6px;
          display: block;
          margin: 0px auto;
          position: relative;
          top: 6px;
          border-radius: 4px;
        }
        .id-card-tag-strip {
          width: 45px;
          height: 40px;
          background-color: #4470f8;
          margin: 0 auto;
          border-radius: 5px;
          position: relative;
          top: 9px;
          z-index: 1;
          border: 1px solid #0041ad;
        }
        .id-card-tag-strip:after {
          content: '';
          display: block;
          width: 100%;
          height: 1px;
          background-color: #c1c1c1;
          position: relative;
          top: 10px;
        }
        .id-card-tag {
          width: 0;
          height: 0;
          border-left: 100px solid transparent;
          border-right: 100px solid transparent;
          border-top: 100px solid #4470f8;
          margin: -10px auto -30px auto;
        }
        .id-card-tag:after {
          content: '';
          display: block;
          width: 0;
          height: 0;
          border-left: 50px solid transparent;
          border-right: 50px solid transparent;
          border-top: 100px solid white;
          margin: -10px auto -30px auto;
          position: relative;
          top: -130px;
          left: -50px;
        }
    </style>
    """), (
    'Sample 2',
    """  <div class="id-card-holder">
        <div class="id-card" id="id-card">
          <div class="header">
            <img id="orgLogo" src="http://untp.realhrsoft.com/static/img/logo/logo-with-tag.png">
          </div>
          <div class="photo">
            <img id="userPP" src="https://i0.wp.com/w.media/wp-content/uploads/2018/01/placeholderhead.jpg">
          </div>
          <h2 id="userName">Name Here</h2>
          <h4 id="userDesignation">Designation Here</h4>
          <h4> Ph: <span id="userPhone"> 9812345678 </span></h4>
          <br>
          <hr>
          <br>
          <p id="orgAddress"> Address Here <p>
          <p>Ph: <span id="orgPhone">9812345678</span> </p>
          <p> Email: <span id="orgEmail">example@email.com </span> </p>
          <p> Issued On: <span id="issuedOn"> 2010-01-01 </span></p>
          <div class="sign">
            <img 
              id="signature" src="https://qph.fs.quoracdn.net/main-qimg-2248bdd01f82b9fb9becdc4bd9a92c53" 
              style="width:100px; height:50px;">
          </div>      
        </div>
      </div>
    <style>
      .id-card-holder {
        width: 225px;
        height: 387px;
        padding: 4px;
        margin: 0 auto;
        background-color: #1f1f1f;
        border-radius: 5px;
        position: relative;
      }
      .id-card {
        background-color: #fff;
        background-size: cover;
        padding: 10px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 0 1.5px 0px #b9b9b9;
      }
      .id-card img {
        margin: 0 auto;
      }
      .header img {
        height: 25px;
        margin-top: 15px;
      }
      .photo img {
        height: 75px;
        margin-top: 15px;
      }
      h2 {
        font-size: 15px;
        margin-top: 5px;
      }
      h3 {
        font-size: 12px;
        margin: 2.5px 0;
        font-weight: 300;
      }
      h4{
        font-size: 10px;
        margin: 0;
        font-weight: 300;
        color: grey;
      }
      .qr-code img {
        width: 50px;
      }
      p {
        font-size: 8px;
        margin: 2px;
      }
      .id-card-hook {
        background-color: #000;
        width: 70px;
        margin: 0 auto;
        height: 15px;
        border-radius: 5px 5px 0 0;
      }
      .id-card-hook:after {
        content: '';
        background-color: #d7d6d3;
        width: 47px;
        height: 6px;
        display: block;
        margin: 0px auto;
        position: relative;
        top: 6px;
        border-radius: 4px;
      }
      .id-card-tag-strip {
        width: 45px;
        height: 40px;
        background-color: #4470f8;
        margin: 0 auto;
        border-radius: 5px;
        position: relative;
        top: 9px;
        z-index: 1;
        border: 1px solid #0041ad;
      }
      .id-card-tag-strip:after {
        content: '';
        display: block;
        width: 100%;
        height: 1px;
        background-color: #c1c1c1;
        position: relative;
        top: 10px;
      }
      .id-card-tag {
        width: 0;
        height: 0;
        border-left: 100px solid transparent;
        border-right: 100px solid transparent;
        border-top: 100px solid #4470f8;
        margin: -10px auto -30px auto;
      }
      .id-card-tag:after {
        content: '';
        display: block;
        width: 0;
        height: 0;
        border-left: 50px solid transparent;
        border-right: 50px solid transparent;
        border-top: 100px solid white;
        margin: -10px auto -30px auto;
        position: relative;
        top: -130px;
        left: -50px;
      }
    </style> 
    """)
]


def seed_samples():
    print("Seeding Id Cards ...")
    created_count = 0
    for name, content in ID_CARD_SAMPLES:
        print(f"Creating {name} ...")
        sample = IdCardSample(name=name, content=content)
        try:
            sample.full_clean()
            sample.save()
            print(f"Created {name}")
            created_count += 1
        except ValidationError as e:
            print(e.messages)
            print(f"Ignoring id-card {name}")
    print(f"Seeding Id Cards complete. Created {created_count} samples.")


class Command(BaseCommand):
    help = "Seed Id Card Samples"

    def handle(self, *args, **kwargs):
        seed_samples()
